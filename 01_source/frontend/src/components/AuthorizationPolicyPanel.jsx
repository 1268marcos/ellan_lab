import React, { useMemo } from "react";

export default function AuthorizationPolicyPanel({ title, markdown, loading, error }) {
  const blocks = useMemo(() => parseSimpleMarkdown(markdown || ""), [markdown]);

  return (
    <section style={containerStyle}>
      <h2 style={titleStyle}>{title || "Política de autorização (fonte única)"}</h2>
      {loading ? <p style={mutedStyle}>Carregando política...</p> : null}
      {error ? <p style={errorStyle}>{error}</p> : null}
      {!loading && !error && !markdown ? (
        <p style={mutedStyle}>Política indisponível no momento.</p>
      ) : null}
      {!loading && !error && markdown ? (
        <div style={{ display: "grid", gap: 8 }}>
          {blocks.map((block, index) => {
            if (block.type === "h2") return <h3 key={index} style={h2Style}>{block.text}</h3>;
            if (block.type === "h3") return <h4 key={index} style={h3Style}>{block.text}</h4>;
            if (block.type === "ul") {
              return (
                <ul key={index} style={listStyle}>
                  {block.items.map((item, itemIdx) => (
                    <li key={itemIdx}>{item}</li>
                  ))}
                </ul>
              );
            }
            if (block.type === "table") {
              return (
                <pre key={index} style={tableStyle}>
                  {block.lines.join("\n")}
                </pre>
              );
            }
            return <p key={index} style={textStyle}>{block.text}</p>;
          })}
        </div>
      ) : null}
    </section>
  );
}

function parseSimpleMarkdown(input) {
  const lines = String(input || "").split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const raw = lines[i];
    const line = raw.trim();

    if (!line) {
      i += 1;
      continue;
    }

    if (line.startsWith("### ")) {
      blocks.push({ type: "h3", text: line.slice(4).trim() });
      i += 1;
      continue;
    }

    if (line.startsWith("## ")) {
      blocks.push({ type: "h2", text: line.slice(3).trim() });
      i += 1;
      continue;
    }

    if (line.startsWith("- ")) {
      const items = [];
      while (i < lines.length && lines[i].trim().startsWith("- ")) {
        items.push(lines[i].trim().slice(2).trim());
        i += 1;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    if (line.startsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i].trim());
        i += 1;
      }
      blocks.push({ type: "table", lines: tableLines });
      continue;
    }

    blocks.push({ type: "p", text: line });
    i += 1;
  }

  return blocks;
}

const containerStyle = {
  border: "1px solid #e2e8f0",
  borderRadius: 12,
  background: "#ffffff",
  padding: 16,
  marginBottom: 16,
};

const titleStyle = {
  marginTop: 0,
  marginBottom: 10,
};

const h2Style = {
  margin: "8px 0 4px",
  fontSize: 18,
};

const h3Style = {
  margin: "6px 0 2px",
  fontSize: 15,
};

const listStyle = {
  margin: "0 0 0 18px",
  color: "#334155",
  display: "grid",
  gap: 4,
};

const textStyle = {
  margin: 0,
  color: "#334155",
  lineHeight: 1.5,
};

const mutedStyle = {
  margin: 0,
  color: "#64748b",
};

const errorStyle = {
  margin: 0,
  color: "#b91c1c",
};

const tableStyle = {
  margin: 0,
  background: "#0f172a",
  color: "#e2e8f0",
  padding: 10,
  borderRadius: 8,
  overflowX: "auto",
  fontSize: 12,
  lineHeight: 1.5,
};
