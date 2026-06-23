// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial
// research and educational use only. Any commercial use, including
// but not limited to use in or for products or services offered for sale,
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

const TABS = {
  inventory: Inventory, mrc: MRC, documents: GovDocs, bibliography: Bibliography,
  audit: Audit, reference: Reference,
};

async function showTab(name) {
  document.querySelectorAll(".tab").forEach(function (b) {
    b.classList.toggle("active", b.getAttribute("data-tab") === name);
  });
  document.querySelectorAll(".panel").forEach(function (p) {
    p.classList.toggle("active", p.id === "tab-" + name);
  });
  try {
    await TABS[name].render();
  } catch (e) {
    App.toast(e.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", async function () {
  document.querySelectorAll(".tab").forEach(function (btn) {
    btn.onclick = function () { showTab(btn.getAttribute("data-tab")); };
  });
  document.getElementById("confirm-ok").onclick = function () { App.confirmPending(); };
  document.getElementById("confirm-cancel").onclick = function () { App.closeConfirm(); };
  // Changing the org scope re-filters the inventory if it's on screen.
  OrgScope.onChange(function () {
    if (document.getElementById("m-list")) Inventory.loadList();
  });
  await OrgScope.init();
  showTab("inventory");
});
