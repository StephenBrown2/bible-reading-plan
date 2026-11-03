// Run with Playwright available to Node; no app dependencies are required.
const { chromium } = require('playwright');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const html = readFileSync(resolve(__dirname, '../index.html'), 'utf8');
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1]
    .replace(/if \(document.readyState === "loading"\)[\s\S]*$/, '');
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
  try {
    for (const mobile of [false, true]) {
      const context = await browser.newContext({
        viewport: { width: mobile ? 390 : 1100, height: 800 },
        isMobile: mobile, hasTouch: mobile,
      });
      const page = await context.newPage();
      page.setDefaultTimeout(5000);
      await page.route('**/*', route => route.abort());
      await page.setContent(html.replace(/<script>[\s\S]*?<\/script>/g, ''));
      await page.addScriptTag({ content: script });
      await page.evaluate(() => {
        document.getElementById('textPanel').classList.add('open');
        document.getElementById('textLoading').hidden = true;
        document.getElementById('passageText').classList.remove('hide-foot', 'hide-xref');
        document.getElementById('passageText').innerHTML = renderVerseStream([
          { verse: 3, text: 'First verse.' },
          { verse: 5, text: '\n\nFirst line\nSecond line\n\nLast paragraph.' },
          { verse: 6, text: '\nNext verse.' },
          { verse: 7, text: 'With a note\u00050\u0005 and reference\u00051\u0005.',
            notes: ['A footnote.', '\u0006A cross-reference.'] },
        ], 2);
      });
      const selected = () => page.evaluate(() => getSelection().toString());
      const clearSelection = async () => {
        await page.evaluate(() => getSelection().removeAllRanges());
        await page.waitForFunction(() => !document.querySelector('.selection-extra.selected'));
        assert.equal(await verse.innerText(), '3First verse.', 'clearing selection restores the normal display');
      };
      const verse = page.locator('.verse').filter({ hasText: 'First verse.' });
      assert.equal(await verse.innerText(), '3First verse.', 'normal display has only the verse number');
      await page.evaluate(() => {
        const addRange = Selection.prototype.addRange;
        window.referenceReadyAtSelection = false;
        Selection.prototype.addRange = function(range) {
          window.referenceReadyAtSelection = [...document.querySelectorAll('.selection-extra')]
            .filter(extra => range.intersectsNode(extra))
            .every(extra => getComputedStyle(extra).display !== 'none');
          return addRange.call(this, range);
        };
      });
      if (mobile) await page.getByText('First verse.', { exact: false }).tap();
      else await page.getByText('First verse.', { exact: false }).click();
      assert.equal(await page.evaluate(() => window.referenceReadyAtSelection), true,
        'reference layout is ready before native selection is installed');
      assert.equal(await selected(), '2:3 First verse.', 'tap selects reference, space and verse');
      assert.equal(await verse.innerText(), '2:3 First verse.', 'selected display includes chapter and space');
      if (mobile) {
        await page.locator('.verse[data-verse="6"]').evaluate(el => {
          el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerType: 'touch' }));
          el.dispatchEvent(new PointerEvent('contextmenu', { bubbles: true, cancelable: true, pointerType: 'touch' }));
        });
        assert.equal((await selected()).replace(/\s+/g, ' ').trim(),
          '2:3 First verse. 2:5 First line Second line Last paragraph. 2:6 Next verse.',
          'touch long-press extends through the target verse');
        const nativeMenuAllowed = await verse.evaluate(el => {
          el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerType: 'touch' }));
          return el.dispatchEvent(new PointerEvent('contextmenu', {
            bubbles: true, cancelable: true, pointerType: 'touch'
          }));
        });
        assert.equal(nativeMenuAllowed, true, 'long-press inside selection keeps the native copy menu');
        await clearSelection();
        await page.locator('.verse[data-verse="6"]').tap();
        await verse.evaluate(el => {
          el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerType: 'touch' }));
          el.dispatchEvent(new PointerEvent('contextmenu', { bubbles: true, cancelable: true, pointerType: 'touch' }));
        });
        assert.equal((await selected()).replace(/\s+/g, ' ').trim(),
          '2:3 First verse. 2:5 First line Second line Last paragraph. 2:6 Next verse.',
          'touch long-press also extends to an earlier verse');
      }
      if (!mobile) {
        await page.keyboard.press('Shift+ArrowLeft');
        assert.notEqual(await selected(), '2:3 First verse.', 'keyboard adjusts the native range');
        await clearSelection();
        const box = await verse.evaluate(el => {
          const range = document.createRange();
          range.setStart(el.lastChild, 0);
          range.setEnd(el.lastChild, 5);
          const rect = range.getBoundingClientRect();
          return { x: rect.x, y: rect.y + rect.height / 2, width: rect.width };
        });
        await page.mouse.move(box.x, box.y);
        await page.mouse.down();
        await page.mouse.move(box.x + box.width, box.y, { steps: 8 });
        await page.mouse.up();
        assert.equal(await selected(), 'First', 'drag keeps the selected word rather than the whole verse');
      }
      await clearSelection();
      const continuation = page.getByText('Second line', { exact: true });
      if (mobile) await continuation.tap(); else await continuation.click();
      assert.equal((await selected()).replace(/\s+/g, ' ').trim(),
        '2:5 First line Second line Last paragraph.', 'continuation selects the entire verse only');
      // A non-collapsed native selection must survive a click used to adjust it.
      await page.evaluate(() => {
        const text = document.querySelector('.verse').lastChild;
        getSelection().setBaseAndExtent(text, 0, text, 5);
        document.querySelector('.verse').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
        document.querySelector('.verse').dispatchEvent(new MouseEvent('click', { bubbles: true, detail: 1 }));
      });
      assert.equal(await selected(), 'First', 'existing selection remains adjustable');
      await clearSelection();
      const annotated = page.locator('.verse[data-verse="7"]');
      if (mobile) await annotated.tap(); else await annotated.click();
      assert.equal(await selected(), '2:7 With a note and reference.', 'selection excludes both kinds of note marker');
      await clearSelection();
      for (const kind of ['foot', 'xref']) {
        const opened = await page.locator(`.note-ref.${kind}`).evaluate(el => {
          el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
          el.dispatchEvent(new MouseEvent('click', { bubbles: true, detail: 1 }));
          return document.getElementById(el.getAttribute('popovertarget')).matches(':popover-open');
        });
        assert.equal(await selected(), '', 'note activation does not select its verse');
        assert.equal(opened, true, `${kind} marker still opens its note`);
      }
      assert.equal(await verse.count(), 1);
      await context.close();
      console.log(`${mobile ? 'Mobile touch' : 'Desktop'} selection checks passed`);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
