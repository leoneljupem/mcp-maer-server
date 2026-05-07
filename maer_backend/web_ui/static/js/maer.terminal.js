/**
 * MAER Terminal Inteligente
 * Emulador web de consola con soporte NLP.
 */

window.MAER = window.MAER || {};

MAER.terminal = {
  cwd: "~",
  history: [],
  historyIndex: -1,

  init: function() {
    console.log("💻 Terminal MAER iniciada");
  },

  send: async function() {
    const input = document.getElementById("term-input");
    const cmd = input.value.trim();
    if (!cmd) return;

    this.history.push(cmd);
    this.historyIndex = this.history.length;
    input.value = "";

    this.print(`\n<span style="color:#ebcb8b">${this.cwd}</span> <span style="color:#a3be8c">❯</span> ${cmd}`);

    const res = await MAER._call("/api/terminal", { command: cmd, cwd: this.cwd });

    if (res.ok) {
      if (res.data.is_nlp) {
        this.print(`<span style="color:#b48ead">MAER ejecutó: ${res.data.command_executed}</span>`);
      }
      if (res.data.cwd) {
        this.cwd = res.data.cwd;
        document.getElementById("term-cwd").innerText = this.cwd.split('/').pop() || '/';
      }
      if (res.data.output) {
        this.print(this.escapeHtml(res.data.output));
      }
    } else {
      this.print(`<span style="color:#bf616a">${res.msg || "Error de ejecución"}</span>`);
      if (res.data && res.data.cwd) this.cwd = res.data.cwd;
    }
  },

  print: function(text) {
    const out = document.getElementById("term-output");
    if (!out) return;
    
    // Add text keeping HTML safe where needed, but here we already formatted tags
    const line = document.createElement("div");
    line.innerHTML = text;
    out.appendChild(line);
    out.scrollTop = out.scrollHeight;
  },

  escapeHtml: function(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
  }
};
