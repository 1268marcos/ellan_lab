function csvEscape(value) {
  const s = value == null ? '' : String(value)
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

export function rowsToCsv(rows, columns) {
  const cols = columns?.length
    ? columns
    : rows[0]
      ? Object.keys(rows[0])
      : []
  const header = cols.join(',')
  const lines = rows.map((row) => cols.map((c) => csvEscape(row[c])).join(','))
  return [header, ...lines].join('\n')
}

export function buildMinimalPdf(title, lines) {
  const esc = (t) =>
    String(t)
      .slice(0, 120)
      .replace(/\\/g, '\\\\')
      .replace(/\(/g, '\\(')
      .replace(/\)/g, '\\)')
  const bodyLines = lines.slice(0, 32).map((line) => `(${esc(line)}) Tj T*`)
  const content = [
    'BT',
    '/F1 14 Tf',
    '72 780 Td',
    `(${esc(title)}) Tj`,
    '/F1 9 Tf',
    '14 TL',
    '72 760 Td',
    ...bodyLines,
    'ET',
  ].join('\n')

  const objects = [
    '1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj',
    '2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj',
    '3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj',
    `4 0 obj<< /Length ${Buffer.byteLength(content, 'utf8')} >>stream\n${content}\nendstream\nendobj`,
    '5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj',
  ]

  let pdf = Buffer.from('%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
  const offsets = [0]
  for (const obj of objects) {
    offsets.push(pdf.length)
    pdf = Buffer.concat([pdf, Buffer.from(`${obj}\n`)])
  }
  const xrefPos = pdf.length
  let xref = `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`
  for (let i = 1; i < offsets.length; i += 1) {
    xref += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`
  }
  const trailer = `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefPos}\n%%EOF\n`
  return Buffer.concat([pdf, Buffer.from(xref + trailer)])
}
