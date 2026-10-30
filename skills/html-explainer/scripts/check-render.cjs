#!/usr/bin/env node
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');

async function inspect(page) {
  return page.evaluate(() => {
    const errors = [];
    const ids = new Set();
    document.querySelectorAll('[id]').forEach(el => {
      if (ids.has(el.id)) errors.push(`duplicate id: ${el.id}`);
      ids.add(el.id);
    });
    document.querySelectorAll('a[href^="#"]').forEach(el => {
      if (!document.getElementById(decodeURIComponent(el.hash.slice(1)))) errors.push(`broken anchor: ${el.hash}`);
    });
    if (document.documentElement.lang !== 'ja') errors.push('lang must be ja');
    if (document.querySelectorAll('h1').length !== 1 || !document.querySelector('main')) errors.push('missing main or unique h1');
    if (document.documentElement.scrollWidth > innerWidth + 1) errors.push(`page overflow: ${document.documentElement.scrollWidth} > ${innerWidth}`);
    document.querySelectorAll('figure').forEach((figure, i) => {
      if (!figure.querySelector('figcaption')?.textContent.trim()) errors.push(`figure ${i}: missing caption`);
      figure.querySelectorAll('*').forEach(el => {
        if (![...el.childNodes].some(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim())) return;
        const s = getComputedStyle(el);
        if (s.fontSize === '0px') errors.push(`figure ${i}: zero-size text`);
      });
    });
    document.querySelectorAll('.chart-fill').forEach((fill, i) => {
      const rect = fill.getBoundingClientRect();
      const track = fill.parentElement.getBoundingClientRect();
      const fraction = parseFloat(fill.style.width) / 100;
      if (fraction > 0 && track.width * fraction > 0.5 && (rect.height < 1 || Math.abs(rect.width - track.width * fraction) > 1.5)) errors.push(`bar ${i}: visible width/height does not match data`);
    });
    document.querySelectorAll('svg').forEach((svg, i) => {
      if (!svg.hasAttribute('viewBox') || !(svg.getAttribute('aria-label') || svg.getAttribute('aria-labelledby'))) errors.push(`SVG ${i}: missing viewBox or label`);
    });
    document.querySelectorAll('table').forEach((table, i) => {
      if (!table.caption || !table.querySelector('th[scope]')) errors.push(`table ${i}: caption or scoped header missing`);
    });
    return {errors, width:innerWidth, pageWidth:document.documentElement.scrollWidth, figures:document.querySelectorAll('figure').length};
  });
}
async function main() {
  const [input, evidence] = process.argv.slice(2);
  if (!input || !evidence) throw new Error('Usage: node check-render.cjs document.html evidence-directory');
  const dest = path.resolve(evidence);
  fs.mkdirSync(dest, {recursive:true});
  const browser = await chromium.launch({headless:true, ...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});
  const report = {input:path.resolve(input), checks:[], errors:[], notes:[]};
  try {
    for (const width of [1440, 390]) {
      for (const theme of ['light', 'dark']) {
        const context = await browser.newContext({viewport:{width,height:1000},colorScheme:theme,reducedMotion:'reduce'});
        const page = await context.newPage();
        page.on('pageerror', e => report.errors.push(e.message));
        await context.route(/^https?:/, route => {report.errors.push(`external dependency: ${route.request().url()}`); return route.abort();});
        await page.goto(pathToFileURL(path.resolve(input)).href);
        await page.emulateMedia({reducedMotion:'reduce'});
        const check = {mode:`${width}-${theme}`, ...await inspect(page)};
        report.checks.push(check);
        report.errors.push(...check.errors.map(e => `${check.mode}: ${e}`));
        const button = page.locator(`[data-theme-set="${theme}"]`);
        if (await button.count()) {
          // On a phone only the current theme button shows and Enter moves to the next; cycle until the wanted one is on.
          for (let i = 0; i < 3 && await button.getAttribute('aria-pressed') !== 'true'; i++) {
            const target = await button.isVisible() ? button : page.locator('[data-theme-set][aria-pressed="true"]');
            await target.focus(); await page.keyboard.press('Enter');
          }
          if (await button.getAttribute('aria-pressed') !== 'true') report.errors.push(`${check.mode}: keyboard theme control failed`);
        }
        await page.screenshot({path:path.join(dest, `${check.mode}.png`),fullPage:true});
        if (theme === 'light') {
          // Every table-of-contents link must bring its section to the top, unless the page cannot scroll further.
          await page.emulateMedia({reducedMotion:'no-preference'});  // the jump must survive smooth scrolling
          for (const hash of await page.$$eval('.toc a[href^="#"]', as => as.map(a => a.getAttribute('href')))) {
            await page.click(`.toc a[href="${hash}"]`); await page.waitForTimeout(1300);
            const [top, atEnd] = await page.evaluate(h => [document.querySelector(h).getBoundingClientRect().top, innerHeight + scrollY >= document.documentElement.scrollHeight - 2], hash);
            if (!(top >= -2 && top < 200) && !atEnd) report.errors.push(`${check.mode}: contents link ${hash} stops ${Math.round(top)}px away`);
          }
          await page.emulateMedia({reducedMotion:'reduce'});
        }
        if (width === 1440 && theme === 'light') {
          await page.emulateMedia({media:'print'});
          await page.screenshot({path:path.join(dest,'print.png'),fullPage:true});
          const print = {mode:'print', ...await inspect(page)};
          const hidden = await page.evaluate(()=>[...document.querySelectorAll('details > :not(summary)')].filter(e=>!e.getBoundingClientRect().height).length);
          if (hidden) print.errors.push(`${hidden} collapsed details blocks print empty`);
          report.checks.push(print);report.errors.push(...print.errors.map(e=>`print: ${e}`));
        }
        await context.close();
      }
    }
    {
      // The first phone screen (390x844) must show the title and the first key point; later points are reported.
      const context = await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
      const page = await context.newPage();
      await page.goto(pathToFileURL(path.resolve(input)).href);
      const fold = await page.evaluate(() => [...document.querySelectorAll('.takeaways li')].map(li => li.getBoundingClientRect().bottom));
      if (fold.length && fold[0] > 844) report.errors.push(`first screen: the first key point ends at ${Math.round(fold[0])}px, below 844px; shorten the title or lead`);
      const below = fold.filter(b => b > 844).length;
      if (below && fold[0] <= 844) report.notes.push(`first screen: ${below} of ${fold.length} key points start or end below 844px; shorten the lead or the key points if they should all show`);
      await page.screenshot({path:path.join(dest,'390-first-screen.png')});
      await context.close();
    }
    const context = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:1000}});
    const page = await context.newPage();
    await page.goto(pathToFileURL(path.resolve(input)).href);
    const nojs = {mode:'no-js', ...await inspect(page)};
    report.checks.push(nojs); report.errors.push(...nojs.errors.map(e=>`no-js: ${e}`));
    await page.screenshot({path:path.join(dest,'no-js.png'),fullPage:true});
    await context.close();
  } finally {
    await browser.close();
    report.passed = report.errors.length === 0;
    fs.writeFileSync(path.join(dest,'report.json'), JSON.stringify(report,null,2)+'\n');
  }
  console.log(JSON.stringify({passed:report.passed,errors:report.errors,notes:report.notes,evidence:dest}));
  process.exitCode = report.passed ? 0 : 1;
}
main().catch(e => { console.error(e.message); process.exitCode=2; });
