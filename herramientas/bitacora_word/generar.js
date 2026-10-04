// Genera la versión Word de la bitácora (docs/bitacora.docx) a partir de docs/bitacora.md.
// La bitácora en Markdown es el documento principal: el Word se regenera cada vez que cambia.
//
// Uso (desde esta carpeta, la primera vez ejecutar "npm install"):
//     npm run generar
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer,
  HeadingLevel, AlignmentType, WidthType, ShadingType, BorderStyle, LevelFormat,
  PageNumber, Bookmark, InternalHyperlink, TableLayoutType, VerticalAlign, UnderlineType,
} = require("docx");

const DIR_DOCS = path.join(__dirname, "..", "..", "docs");
const SRC = process.argv[2] || path.join(DIR_DOCS, "bitacora.md");
const OUT = process.argv[3] || path.join(DIR_DOCS, "bitacora.docx");
const SUBTITULO = "Análisis de reingresos hospitalarios mediante selección de variables sobre datos GRD";

// A4 con márgenes de 1" (el informe de la tesis está en A4).
const PAGE_W = 11906, PAGE_H = 16838, MARGEN = 1440;
const ANCHO = PAGE_W - 2 * MARGEN;               // 9026
const ANCHO_ETIQUETA = 1800;
const ANCHO_CONTENIDO = ANCHO - ANCHO_ETIQUETA;  // 7026
const PAD = 100;                                 // margen interno de celdas (izq./der.)
const ANCHO_ANIDADA = ANCHO_CONTENIDO - 2 * PAD;

const AZUL = "1F3864", GRIS = "808080", BORDE = "BFBFBF";
const TIPOS = {
  H: { etiqueta: "Hallazgo", color: "2E75B6" },
  D: { etiqueta: "Decisión", color: "548235" },
  C: { etiqueta: "Corrección al informe", color: "C55A11" },
};
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
  "septiembre", "octubre", "noviembre", "diciembre"];
const fechaLarga = (iso) => {
  const [a, m, d] = iso.split("-").map(Number);
  return `${d} de ${MESES[m - 1]} de ${a}`;
};

// ---------------------------------------------------------------- lectura del Markdown
const L = fs.readFileSync(SRC, "utf8").replace(/\r\n/g, "\n").split("\n");
const esTabla = (s) => /^\s*\|/.test(s);

function dividirFila(r) {
  r = r.trim();
  if (r.startsWith("|")) r = r.slice(1);
  if (r.endsWith("|")) r = r.slice(0, -1);
  const out = [];
  let cur = "", enCodigo = false;
  for (const ch of r) {
    if (ch === "`") enCodigo = !enCodigo;
    if (ch === "|" && !enCodigo) { out.push(cur.trim()); cur = ""; } else cur += ch;
  }
  out.push(cur.trim());
  return out;
}

function leerTabla(i) {
  const filas = [];
  while (i < L.length && esTabla(L[i])) {
    const t = L[i].trim();
    if (!/^\|[\s:|-]+\|?$/.test(t)) filas.push(dividirFila(t)); // omite la fila separadora
    i++;
  }
  return [filas, i];
}

function leerEntrada(i) {
  const partes = L[i].replace(/^###\s+/, "").trim().split(" · ");
  const conFecha = partes.length >= 3 && /^\d{4}-\d{2}-\d{2}$/.test(partes[1]);
  const entrada = {
    tipo: "entrada", id: partes[0], fecha: conFecha ? partes[1] : null,
    titulo: partes.slice(conFecha ? 2 : 1).join(" · "), campos: [],
  };
  let cur = null, corte = false, j = i + 1;
  const campoActual = () => {
    if (!cur) { cur = { etiqueta: "", bloques: [] }; entrada.campos.push(cur); }
    return cur;
  };
  while (j < L.length && !/^(#{1,3}\s|---\s*$)/.test(L[j])) {
    const s = L[j];
    const m = s.match(/^- \*\*(.+?):\*\*\s*(.*)$/);
    if (m) {
      cur = { etiqueta: m[1], bloques: m[2] ? [{ tipo: "parrafo", texto: m[2] }] : [] };
      entrada.campos.push(cur); corte = false; j++; continue;
    }
    if (/^- /.test(s)) {
      cur = { etiqueta: "", bloques: [{ tipo: "parrafo", texto: s.slice(2) }] };
      entrada.campos.push(cur); corte = false; j++; continue;
    }
    if (s.trim() === "") { corte = true; j++; continue; }
    if (esTabla(s)) {
      const [filas, k] = leerTabla(j);
      campoActual().bloques.push({ tipo: "tabla", filas });
      corte = true; j = k; continue;
    }
    const c = campoActual();
    const ultimo = c.bloques[c.bloques.length - 1];
    if (!corte && ultimo && ultimo.tipo === "parrafo") ultimo.texto += " " + s.trim();
    else c.bloques.push({ tipo: "parrafo", texto: s.trim() });
    corte = false; j++;
  }
  return [entrada, j];
}

const bloques = [];
for (let i = 0; i < L.length;) {
  const s = L[i];
  if (/^#\s/.test(s)) { bloques.push({ tipo: "titulo", texto: s.replace(/^#\s+/, "").trim() }); i++; }
  else if (/^##\s/.test(s)) { bloques.push({ tipo: "h1", texto: s.replace(/^##\s+/, "").trim() }); i++; }
  else if (/^###\s/.test(s)) { const [e, j] = leerEntrada(i); bloques.push(e); i = j; }
  else if (/^---\s*$/.test(s) || s.trim() === "") i++;
  else if (esTabla(s)) { const [filas, j] = leerTabla(i); bloques.push({ tipo: "tabla", filas }); i = j; }
  else if (/^- \[[ xX]\] /.test(s)) {
    bloques.push({ tipo: "tarea", hecha: /^- \[[xX]\]/.test(s), texto: s.replace(/^- \[[ xX]\] /, "") }); i++;
  } else if (/^- /.test(s)) { bloques.push({ tipo: "vineta", texto: s.slice(2) }); i++; }
  else {
    const partes = [s.trim()];
    i++;
    while (i < L.length && L[i].trim() !== "" && !/^(#|---|\||- )/.test(L[i].trim())) partes.push(L[i++].trim());
    bloques.push({ tipo: "parrafo", texto: partes.join(" ") });
  }
}

const entradas = bloques.filter((b) => b.tipo === "entrada");
const IDS = new Set(entradas.map((e) => e.id));
const fechas = entradas.map((e) => e.fecha).filter(Boolean).sort();
const ultimaFecha = fechas[fechas.length - 1];

// ---------------------------------------------------------------- texto con formato
// Convierte **negrita**, *cursiva* y `código`; las menciones a entradas (H01, D03...)
// fuera del código se vuelven vínculos a la entrada correspondiente.
function conVinculos(texto, base) {
  const out = [];
  const re = /\b([HDC]\d{2})\b(?!\.\d)/g;
  let ultimo = 0, m;
  while ((m = re.exec(texto))) {
    if (!IDS.has(m[1])) continue;
    if (m.index > ultimo) out.push(new TextRun({ ...base, text: texto.slice(ultimo, m.index) }));
    out.push(new InternalHyperlink({
      anchor: `E_${m[1]}`,
      children: [new TextRun({ ...base, text: m[1], color: "0563C1", underline: { type: UnderlineType.SINGLE } })],
    }));
    ultimo = m.index + m[1].length;
  }
  if (ultimo < texto.length) out.push(new TextRun({ ...base, text: texto.slice(ultimo) }));
  return out;
}

function runs(texto, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let ultimo = 0, m;
  while ((m = re.exec(texto))) {
    if (m.index > ultimo) out.push(...conVinculos(texto.slice(ultimo, m.index), base));
    const t = m[0];
    if (t.startsWith("**")) out.push(...conVinculos(t.slice(2, -2), { ...base, bold: true }));
    else if (t.startsWith("`")) {
      out.push(new TextRun({
        ...base, text: t.slice(1, -1), font: "Consolas", size: (base.size || 22) - 2,
        shading: { type: ShadingType.CLEAR, fill: "F2F2F2", color: "auto" },
      }));
    } else out.push(...conVinculos(t.slice(1, -1), { ...base, italics: true }));
    ultimo = m.index + t.length;
  }
  if (ultimo < texto.length) out.push(...conVinculos(texto.slice(ultimo), base));
  return out;
}

const textoPlano = (s) => s.replace(/\*\*|`|\*/g, "");

// ---------------------------------------------------------------- tablas
const bordes = {
  top: { style: BorderStyle.SINGLE, size: 4, color: BORDE },
  bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDE },
  left: { style: BorderStyle.SINGLE, size: 4, color: BORDE },
  right: { style: BorderStyle.SINGLE, size: 4, color: BORDE },
  insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: BORDE },
  insideVertical: { style: BorderStyle.SINGLE, size: 4, color: BORDE },
};
const margenesCelda = { top: 70, bottom: 70, left: PAD, right: PAD };

// Ancho de columnas proporcional al contenido, sin bajar del ancho de la palabra más larga.
function anchosColumnas(filas, total, tamFuente) {
  const n = Math.max(...filas.map((f) => f.length));
  const car = tamFuente * 5.4;  // ancho aproximado de un carácter en DXA
  const largo = [], palabra = [];
  for (let c = 0; c < n; c++) {
    const textos = filas.map((f) => textoPlano(f[c] || ""));
    largo.push(Math.min(Math.max(...textos.map((t) => t.length), 3), 60));
    palabra.push(Math.min(Math.max(...textos.flatMap((t) => t.split(/\s+/)).map((w) => w.length), 3), 18));
  }
  const natural = largo.map((l) => l * car + 2 * PAD);
  const minimo = palabra.map((l) => l * car * 1.2 + 2 * PAD);
  const suma = natural.reduce((a, b) => a + b, 0);
  let w = natural.map((x) => (x * total) / suma);
  let deficit = 0;
  w = w.map((x, i) => (x < minimo[i] ? ((deficit += minimo[i] - x), minimo[i]) : x));
  const holgura = w.reduce((s, x, i) => s + Math.max(0, x - minimo[i]), 0);
  if (deficit > 0 && holgura > 0) w = w.map((x, i) => x - (deficit * Math.max(0, x - minimo[i])) / holgura);
  w = w.map(Math.floor);
  w[w.length - 1] += total - w.reduce((a, b) => a + b, 0);
  return w;
}

function tablaSimple(filas, total, tamFuente) {
  const anchos = anchosColumnas(filas, total, tamFuente);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: anchos,
    layout: TableLayoutType.FIXED,
    borders: bordes,
    rows: filas.map((fila, r) => new TableRow({
      tableHeader: r === 0,
      cantSplit: true,
      children: anchos.map((ancho, c) => new TableCell({
        width: { size: ancho, type: WidthType.DXA },
        margins: margenesCelda,
        verticalAlign: VerticalAlign.CENTER,
        shading: r === 0 ? { type: ShadingType.CLEAR, fill: "D9E2F3", color: "auto" } : undefined,
        children: [new Paragraph({
          spacing: { after: 0 },
          children: runs(fila[c] || "", { size: tamFuente, bold: r === 0 ? true : undefined }),
        })],
      })),
    })),
  });
}

// Ficha de una entrada: una fila por campo (Actividad, Decisión, Evidencia, Estado...).
function ficha(campos) {
  return new Table({
    width: { size: ANCHO, type: WidthType.DXA },
    columnWidths: [ANCHO_ETIQUETA, ANCHO_CONTENIDO],
    layout: TableLayoutType.FIXED,
    borders: bordes,
    rows: campos.map((campo, idx) => {
      const mantener = idx < campos.length - 1;  // mantiene la ficha en una sola página
      const contenido = [];
      campo.bloques.forEach((b, k) => {
        const ultimo = k === campo.bloques.length - 1;
        if (b.tipo === "parrafo") {
          const trasTabla = k > 0 && campo.bloques[k - 1].tipo === "tabla";
          contenido.push(new Paragraph({
            keepNext: mantener,
            spacing: { before: trasTabla ? 100 : 0, after: ultimo ? 0 : 80 },
            children: runs(b.texto, { size: 20 }),
          }));
        } else {
          contenido.push(tablaSimple(b.filas, ANCHO_ANIDADA, 18));
          if (ultimo) contenido.push(new Paragraph({ spacing: { after: 0 }, children: [] }));
        }
      });
      if (!contenido.length) contenido.push(new Paragraph({ children: [] }));
      return new TableRow({
        cantSplit: true,
        children: [
          new TableCell({
            width: { size: ANCHO_ETIQUETA, type: WidthType.DXA },
            margins: margenesCelda,
            shading: { type: ShadingType.CLEAR, fill: "F2F2F2", color: "auto" },
            children: [new Paragraph({
              keepNext: mantener, spacing: { after: 0 },
              children: [new TextRun({ text: campo.etiqueta, bold: true, size: 20, color: "404040" })],
            })],
          }),
          new TableCell({
            width: { size: ANCHO_CONTENIDO, type: WidthType.DXA },
            margins: margenesCelda,
            children: contenido,
          }),
        ],
      });
    }),
  });
}

// ---------------------------------------------------------------- documento
const hijos = [];
let entradasIniciadas = false;
for (const b of bloques) {
  if (b.tipo === "titulo") {
    hijos.push(new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun(b.texto)] }));
    hijos.push(new Paragraph({
      spacing: { after: 60 },
      children: [new TextRun({ text: SUBTITULO, italics: true, color: "595959", size: 24 })],
    }));
    hijos.push(new Paragraph({
      spacing: { after: 280 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: AZUL, space: 6 } },
      children: [new TextRun({
        text: `Actualizada al ${fechaLarga(ultimaFecha)} · Versión Word generada a partir de Codigo/docs/bitacora.md`,
        color: GRIS, size: 18,
      })],
    }));
  } else if (b.tipo === "h1") {
    hijos.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(b.texto)] }));
  } else if (b.tipo === "entrada") {
    if (!entradasIniciadas) {
      hijos.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Entradas")] }));
      entradasIniciadas = true;
    }
    const tipo = TIPOS[b.id[0]] || { etiqueta: "Entrada", color: AZUL };
    hijos.push(new Paragraph({
      heading: HeadingLevel.HEADING_2,
      children: [
        new Bookmark({ id: `E_${b.id}`, children: [new TextRun({ text: b.id, color: tipo.color })] }),
        new TextRun(` · ${b.titulo}`),
      ],
    }));
    hijos.push(new Paragraph({
      keepNext: true,
      spacing: { after: 100 },
      children: [
        new TextRun({ text: tipo.etiqueta, bold: true, color: tipo.color, size: 18 }),
        new TextRun({ text: b.fecha ? `  ·  ${fechaLarga(b.fecha)}` : "", color: GRIS, size: 18 }),
      ],
    }));
    if (b.campos.length) hijos.push(ficha(b.campos));
  } else if (b.tipo === "tabla") {
    hijos.push(tablaSimple(b.filas, ANCHO, 20));
    hijos.push(new Paragraph({ spacing: { after: 0 }, children: [] }));
  } else if (b.tipo === "tarea") {
    hijos.push(new Paragraph({
      numbering: { reference: b.hecha ? "hecha" : "pendiente", level: 0 },
      spacing: { after: 80 },
      children: runs(b.texto),
    }));
  } else if (b.tipo === "vineta") {
    hijos.push(new Paragraph({ numbering: { reference: "vinetas", level: 0 }, children: runs(b.texto) }));
  } else if (b.tipo === "parrafo") {
    hijos.push(new Paragraph({ children: runs(b.texto) }));
  }
}

const vineta = (ref, simbolo, fuente) => ({
  reference: ref,
  levels: [{
    level: 0, format: LevelFormat.BULLET, text: simbolo, alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 500, hanging: 360 } }, run: fuente ? { font: fuente } : undefined },
  }],
});

const estiloTitulo = (id, nombre, tam, antes, despues, nivel) => ({
  id, name: nombre, basedOn: "Normal", next: "Normal", quickFormat: true,
  run: { font: "Calibri", size: tam, bold: true, color: AZUL },
  paragraph: { spacing: { before: antes, after: despues }, keepNext: true, keepLines: true, outlineLevel: nivel },
});

const doc = new Document({
  creator: "Tesis GRD",
  title: "Bitácora de decisiones sobre los datos",
  description: "Hallazgos y decisiones del procesamiento de la base GRD 2019–2024",
  styles: {
    default: {
      document: {
        run: { font: "Calibri", size: 22, language: { value: "es-CL" } },
        paragraph: { spacing: { after: 120, line: 276 } },
      },
    },
    paragraphStyles: [
      { ...estiloTitulo("Title", "Title", 40, 0, 60, undefined) },
      estiloTitulo("Heading1", "Heading 1", 30, 400, 160, 0),
      estiloTitulo("Heading2", "Heading 2", 24, 320, 40, 1),
    ],
  },
  numbering: {
    config: [
      vineta("pendiente", "☐", "Segoe UI Symbol"),
      vineta("hecha", "☑", "Segoe UI Symbol"),
      vineta("vinetas", "•"),
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: PAGE_W, height: PAGE_H }, margin: { top: MARGEN, right: MARGEN, bottom: MARGEN, left: MARGEN } },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "Bitácora de decisiones · Reingresos hospitalarios GRD 2019–2024", color: GRIS, size: 16 })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: ["Página ", PageNumber.CURRENT, " de ", PageNumber.TOTAL_PAGES], color: GRIS, size: 16 })],
        })],
      }),
    },
    children: hijos,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log(`OK: ${OUT} (${entradas.length} entradas, ${buf.length.toLocaleString("es-CL")} bytes)`);
});
