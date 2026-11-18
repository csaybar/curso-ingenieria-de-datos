// Exporta unas slides a PDF, una página por slide.
// Requiere Node y Playwright:  npm install playwright && npx playwright install chromium
// Uso, desde la raíz del repo:  node fuentes/pdf.js clase-01/slides.html clase-01/slides.pdf
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const navegador = await chromium.launch();
  const pagina = await (await navegador.newContext({ offline: true })).newPage();
  await pagina.goto('file://' + path.resolve(process.argv[2]));
  await pagina.waitForTimeout(500);
  await pagina.emulateMedia({ media: 'print' });
  await pagina.pdf({ path: process.argv[3], preferCSSPageSize: true, printBackground: true });
  await navegador.close();
})();
