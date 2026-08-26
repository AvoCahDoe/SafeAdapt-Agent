"use client";

import katex from "katex";
import "katex/dist/katex.min.css";

type MathProps = {
  tex: string;
  block?: boolean;
  className?: string;
};

export function Formula({ tex, block = false, className }: MathProps) {
  const html = katex.renderToString(tex, {
    throwOnError: false,
    displayMode: block,
  });

  if (block) {
    return (
      <div
        className={`math-block ${className ?? ""}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

  return (
    <span
      className={`math-inline ${className ?? ""}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
