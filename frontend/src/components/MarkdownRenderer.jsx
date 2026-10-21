import React from 'react';

/**
 * Lightweight, safe React Markdown renderer.
 * Formats headings, bold, italics, inline code, fenced code blocks,
 * ordered & unordered lists, blockquotes, and tables without external dependencies.
 */
export default function MarkdownRenderer({ content = '' }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let index = 0;

  const renderInline = (text) => {
    if (!text) return '';
    // Format bold + italic ***text***
    let parts = [text];

    // Helper for replacing pattern with React elements
    const replaceWithComponent = (currentParts, regex, componentFn) => {
      const result = [];
      for (const part of currentParts) {
        if (typeof part !== 'string') {
          result.push(part);
          continue;
        }
        let lastIdx = 0;
        let match;
        const re = new RegExp(regex);
        while ((match = re.exec(part)) !== null) {
          if (match.index > lastIdx) {
            result.push(part.substring(lastIdx, match.index));
          }
          result.push(componentFn(match[1] || match[0], result.length));
          lastIdx = match.index + match[0].length;
        }
        if (lastIdx < part.length) {
          result.push(part.substring(lastIdx));
        }
      }
      return result;
    };

    // Code `...`
    parts = replaceWithComponent(parts, /`([^`]+)`/g, (match, i) => (
      <code key={`code-${i}`} className="bg-light text-danger px-1 py-0.5 rounded small">{match}</code>
    ));

    // Bold **...**
    parts = replaceWithComponent(parts, /\*\*([^*]+)\*\*/g, (match, i) => (
      <strong key={`b-${i}`}>{match}</strong>
    ));

    // Italic *...*
    parts = replaceWithComponent(parts, /(?<!\*)\*([^*]+)\*(?!\*)/g, (match, i) => (
      <em key={`i-${i}`}>{match}</em>
    ));

    return parts;
  };

  while (index < lines.length) {
    const line = lines[index];

    // 1. Code blocks ```
    if (line.trim().startsWith('```')) {
      const codeLines = [];
      index++;
      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        codeLines.push(lines[index]);
        index++;
      }
      index++; // skip closing ```
      elements.push(
        <pre key={`pre-${index}`} className="bg-dark text-light p-3 rounded small overflow-auto my-2">
          <code>{codeLines.join('\n')}</code>
        </pre>
      );
      continue;
    }

    // 2. Headings
    if (line.startsWith('### ')) {
      elements.push(<h6 key={`h6-${index}`} className="fw-bold mt-3 mb-1 text-primary">{renderInline(line.substring(4))}</h6>);
      index++;
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(<h5 key={`h5-${index}`} className="fw-bold mt-3 mb-2 text-dark">{renderInline(line.substring(3))}</h5>);
      index++;
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(<h4 key={`h4-${index}`} className="fw-bold mt-3 mb-2 text-dark">{renderInline(line.substring(2))}</h4>);
      index++;
      continue;
    }

    // 3. Blockquotes
    if (line.startsWith('> ')) {
      elements.push(
        <blockquote key={`bq-${index}`} className="border-start border-3 border-primary ps-3 py-1 my-2 text-muted fst-italic bg-light rounded-end">
          {renderInline(line.substring(2))}
        </blockquote>
      );
      index++;
      continue;
    }

    // 4. Tables
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const tableRows = [];
      while (index < lines.length && lines[index].trim().startsWith('|') && lines[index].trim().endsWith('|')) {
        const rowText = lines[index].trim();
        // check if separator row |--|--|
        if (!rowText.match(/^\|[\s-:]+\|$/) && !rowText.includes('---')) {
          const cells = rowText.split('|').slice(1, -1).map(c => c.trim());
          tableRows.push(cells);
        }
        index++;
      }

      if (tableRows.length > 0) {
        const headerCells = tableRows[0];
        const bodyRows = tableRows.slice(1);
        elements.push(
          <div key={`table-${index}`} className="table-responsive my-2">
            <table className="table table-sm table-bordered table-striped small mb-0">
              <thead className="table-light">
                <tr>
                  {headerCells.map((cell, cIdx) => (
                    <th key={`th-${cIdx}`}>{renderInline(cell)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bodyRows.map((row, rIdx) => (
                  <tr key={`tr-${rIdx}`}>
                    {row.map((cell, cIdx) => (
                      <td key={`td-${rIdx}-${cIdx}`}>{renderInline(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      continue;
    }

    // 5. Unordered lists
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      const listItems = [];
      while (index < lines.length && (lines[index].trim().startsWith('- ') || lines[index].trim().startsWith('* '))) {
        listItems.push(lines[index].trim().substring(2));
        index++;
      }
      elements.push(
        <ul key={`ul-${index}`} className="mb-2 ps-3 small">
          {listItems.map((item, liIdx) => (
            <li key={`li-${liIdx}`} className="mb-1">{renderInline(item)}</li>
          ))}
        </ul>
      );
      continue;
    }

    // 6. Ordered lists
    if (line.match(/^\d+\.\s+/)) {
      const listItems = [];
      while (index < lines.length && lines[index].match(/^\d+\.\s+/)) {
        const itemText = lines[index].replace(/^\d+\.\s+/, '');
        listItems.push(itemText);
        index++;
      }
      elements.push(
        <ol key={`ol-${index}`} className="mb-2 ps-3 small">
          {listItems.map((item, liIdx) => (
            <li key={`oli-${liIdx}`} className="mb-1">{renderInline(item)}</li>
          ))}
        </ol>
      );
      continue;
    }

    // 7. Regular paragraph / empty line
    if (!line.trim()) {
      index++;
      continue;
    }

    elements.push(
      <p key={`p-${index}`} className="mb-2">
        {renderInline(line)}
      </p>
    );
    index++;
  }

  return <div className="markdown-body">{elements}</div>;
}
