import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// 5.2 · Auditoría automática de accesibilidad (WCAG 2.1 A/AA) de las páginas públicas y del área privada.
const PAGES = ["/", "/analisis", "/comparar", "/demo", "/normativa", "/avance", "/fuentes", "/login", "/campo"];

for (const path of PAGES) {
  test(`accesibilidad WCAG 2.1 AA: ${path}`, async ({ page }) => {
    await page.goto(path);
    await page.waitForTimeout(3500); // el mapa sigue pidiendo teselas: no esperar a «networkidle»
    const r = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .exclude(".maplibregl-canvas") // el lienzo del mapa no es texto; su alternativa es la lista de municipios
      .analyze();
    const serious = r.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious.map((v) => `${v.id}: ${v.nodes.length} × ${v.nodes[0]?.target.join(" ")}`)).toEqual([]);
  });
}

test("accesibilidad WCAG 2.1 AA: área de trabajo con sesión (plan, expediente y decisiones)", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill("gestor@demo.escudo.local");
  await page.getByLabel("Contraseña").fill("demo-escudo-2026");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await page.getByRole("button", { name: /Urbanización Ejemplo Los Pinos/ }).click();
  for (const tab of ["Contexto", "Inspecciones", "Escenarios y plan", "Expediente", "Decisiones"]) {
    await page.getByRole("tab", { name: tab }).click();
    await page.waitForTimeout(1500);
    const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    expect(r.violations.map((v) => `${tab} · ${v.impact}:${v.id} ${v.nodes[0]?.target.join(" ")}`)).toEqual([]);
  }
});

test.describe("móvil (390 px): sin desbordamiento horizontal", () => {
  test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  for (const path of ["/", "/analisis", "/demo", "/normativa", "/avance", "/fuentes", "/campo"]) {
    test(`sin scroll horizontal: ${path}`, async ({ page }) => {
      await page.goto(path);
      await page.waitForTimeout(2500);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow).toBeLessThanOrEqual(1);
    });
  }
});
