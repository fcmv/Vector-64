import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { BootScreen } from "./BootScreen";

describe("engine boot screen", () => {
  it("shows an actionable error instead of an endless progress bar", () => {
    const html = renderToStaticMarkup(<BootScreen error="Enable isolation and reload." />);
    expect(html).toContain('role="alert"');
    expect(html).toContain("Enable isolation and reload.");
    expect(html).toContain("Reload</button>");
    expect(html).not.toContain("evalbar");
  });

  it("escapes error text", () => {
    const html = renderToStaticMarkup(<BootScreen error={'<script>alert("bad")</script>'} />);
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;");
  });

  it("keeps network progress and notes visible while loading", () => {
    const html = renderToStaticMarkup(<BootScreen p={{ phase: "net", loaded: 25, total: 100, note: "Downloading" }} />);
    expect(html).toContain("25%");
    expect(html).toContain("network");
    expect(html).toContain("Downloading");
    expect(html).not.toContain('role="alert"');
  });
});
