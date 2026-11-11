import { expect, test } from "@playwright/test";

// 1×1 PNG válido
const PNG = Buffer.from("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6390b3d6ff0f00028b0188aca22bc10000000049454e44ae426082", "hex");

test("M21 campo: inspección sin conexión, página servida offline y envío único al volver la red", async ({ page, context }) => {
  const stamp = `Campo e2e ${Date.now()} (ficticio)`;
  await page.goto("/login?next=/campo");
  await page.getByLabel("Correo electrónico").fill("gestor@demo.escudo.local");
  await page.getByLabel("Contraseña").fill("demo-escudo-2026");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/campo$/);
  await expect(page.getByText("Ámbitos y lista guardados", { exact: false })).toBeVisible();
  await page.evaluate(() => navigator.serviceWorker.ready);

  await context.setOffline(true);
  await expect(page.getByText("Sin conexión", { exact: true })).toBeVisible();
  await page.getByLabel("Ámbito").selectOption({ label: "Urbanización Ejemplo Los Pinos (FICTICIA)" });
  await page.getByLabel("Persona que inspecciona").fill(stamp);
  await page.getByRole("radiogroup").first().getByText("Parcial").click();
  await page.getByLabel("Fotos (JPG o PNG, hasta 5)").setInputFiles({ name: "campo.png", mimeType: "image/png", buffer: PNG });
  await page.getByRole("button", { name: "Guardar inspección" }).click();
  await expect(page.getByText("guardada en el dispositivo", { exact: false })).toBeVisible();
  await expect(page.getByText("1 pendiente de enviar")).toBeVisible();

  // la página abre sin conexión (service worker) y la cola sigue ahí
  await page.reload();
  await expect(page.getByRole("heading", { name: "Inspección en campo" })).toBeVisible();
  await expect(page.getByText("1 pendiente de enviar")).toBeVisible();

  await context.setOffline(false);
  await expect(page.getByText("0 pendientes de enviar")).toBeVisible({ timeout: 20_000 });

  const token = await page.evaluate(() => sessionStorage.getItem("escudo.token"));
  const api = process.env.E2E_API_URL || "http://localhost:8010";
  const areas = await (await page.request.get(`${api}/v1/areas`, { headers: { Authorization: `Bearer ${token}` } })).json();
  const area = areas.find((a: { name: string }) => a.name.includes("Los Pinos"));
  const list = await (await page.request.get(`${api}/v1/inspections?area_id=${area.id}`, { headers: { Authorization: `Bearer ${token}` } })).json();
  const mine = list.filter((i: { inspector_name: string }) => i.inspector_name === stamp);
  expect(mine).toHaveLength(1);
  expect(mine[0].evidence).toHaveLength(1);
});
