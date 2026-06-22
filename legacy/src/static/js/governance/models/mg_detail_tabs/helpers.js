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

// ================================================================
// HTML helpers
// ================================================================
function sectionHeader(text) {
    return '<div style="font-size:11px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.5px;margin-top:16px;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #eee;">' + text + '</div>';
}

function infoRow(label, value) {
    return '<div style="display:flex;padding:3px 0;font-size:11px;">' +
        '<span style="min-width:130px;color:#888;flex-shrink:0;">' + label + '</span>' +
        '<span style="color:#333;">' + value + '</span></div>';
}
