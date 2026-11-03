// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
// Loads after helpers.js, before model_docs.js and doc_panel.js.

// The upload row both document renderers share: a document is filed either as a
// file or as a link, under the same category and with the same description, and the
// server treats the two alike (src/web/_document_upload.py). `p` prefixes every id
// so several rows can sit on one screen.
const DocUpload = {
  // `small` sizes the inputs for the inline panels; the Docs tab uses full size.
  html(p, small) {
    const fs = small ? "font-size:var(--size-sm);" : "";
    return '<select id="' + p + '-kind" style="' + fs + '">' +
      '<option value="file">File</option><option value="link">Link</option></select>' +
      '<input type="file" id="' + p + '-file" style="' + fs + '">' +
      '<input id="' + p + '-url" type="url" placeholder="https://…" hidden style="' + fs + 'flex:1">' +
      '<input id="' + p + '-title" placeholder="Name (optional)" hidden style="' + fs + '">' +
      '<input id="' + p + '-desc" placeholder="Description (optional)" style="' + fs + 'flex:1">' +
      '<button class="btn small primary" id="' + p + '-upload">Upload</button>';
  },

  // Show the inputs for the chosen kind, and run `onUpload` from the button.
  bind(p, onUpload) {
    const kind = document.getElementById(p + "-kind");
    const button = document.getElementById(p + "-upload");
    if (!kind || !button) return;
    kind.onchange = function () {
      const link = kind.value === "link";
      document.getElementById(p + "-file").hidden = link;
      document.getElementById(p + "-url").hidden = !link;
      document.getElementById(p + "-title").hidden = !link;
      button.textContent = link ? "Add link" : "Upload";
    };
    button.onclick = onUpload;
  },

  // POST the row to `<base><id>/documents` under `category`, then `refresh`.
  submit(p, url, category, refresh) {
    const form = new FormData();
    const link = document.getElementById(p + "-kind").value === "link";
    if (link) {
      const address = document.getElementById(p + "-url").value.trim();
      if (!address) { App.toast("Enter a link first", "error"); return; }
      form.append("url", address);
      form.append("title", document.getElementById(p + "-title").value);
    } else {
      const fileInput = document.getElementById(p + "-file");
      if (!fileInput.files.length) { App.toast("Choose a file first", "error"); return; }
      form.append("file", fileInput.files[0]);
    }
    form.append("category", category);
    form.append("description", document.getElementById(p + "-desc").value);
    fetch(url, {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast(link ? "Link added" : "Document uploaded", "ok");
      refresh();
    }).catch((e) => App.toast(e.message, "error"));
  },
};
