"""
Run:
    streamlit run app.py
"""

import re
from io import BytesIO
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import streamlit as st
from pypdf import PdfReader, PdfWriter

def human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    kb = num_bytes / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    mb = kb / 1024
    return f"{mb:.2f} MB"

def parse_page_ranges(range_str: str, num_pages: int) -> Tuple[List[int], Optional[str]]:
    s = (range_str or "").strip()
    if not s:
        return list(range(num_pages)), None

    indices: List[int] = []
    tokens = [t.strip() for t in s.split(",") if t.strip()]
    if not tokens:
        return list(range(num_pages)), None

    for tok in tokens:
        if "-" in tok:
            parts = [p.strip() for p in tok.split("-", 1)]
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                return [], f"Invalid range token: '{tok}'"
            start = int(parts[0])
            end = int(parts[1])
            if start < 1 or end < 1 or start > end:
                return [], f"Invalid range values in '{tok}' (use like 2-5)"
            if end > num_pages:
                return [], f"Range '{tok}' exceeds page count ({num_pages})"
            indices.extend(list(range(start - 1, end)))
        else:
            if not tok.isdigit():
                return [], f"Invalid page token: '{tok}'"
            page = int(tok)
            if page < 1 or page > num_pages:
                return [], f"Page '{tok}' out of bounds (1..{num_pages})"
            indices.append(page - 1)

    # Remove duplicates while preserving order
    seen = set()
    deduped = []
    for i in indices:
        if i not in seen:
            seen.add(i)
            deduped.append(i)

    return deduped, None

@dataclass
class FileMeta:
    file_id: str
    name: str
    size: int
    num_pages: int

def build_file_id(uploaded_file) -> str:
    return f"{uploaded_file.name}__{uploaded_file.size}"

def try_sortables(order_names: List[str]) -> Optional[List[str]]:
    """
    If streamlit-sortables is available, returns a possibly reordered list via drag-drop.
    Otherwise returns None.
    """
    try:
        from streamlit_sortables import sort_items  # type: ignore

        st.caption("Drag & drop to reorder:")
        new_order = sort_items(order_names, direction="vertical")
        if isinstance(new_order, list) and new_order:
            return new_order
        return order_names
    except Exception:
        return None

def main():
    st.set_page_config(page_title="PDF Binder", page_icon="📄", layout="centered")

    st.title("📄 PDF Binder Tool")
    st.write("Upload PDF files, reorder them, optionally select page ranges, and merge into one PDF. Don't worry about sending your data to external servers or weird websites.")

    with st.sidebar:
        st.header("Options")
        output_name = st.text_input("Output filename", value="merged_document.pdf")
        if not output_name.lower().endswith(".pdf"):
            output_name += ".pdf"

        merge_mode = st.selectbox(
            "Merge mode",
            options=["All pages", "Select page ranges"],
            index=0,
            help="Choose whether to merge entire PDFs or only selected pages from each.",
        )

        st.caption(
            "Tip: In *Select page ranges* mode, use formats like `1-3,5,8-10`."
        )

        st.divider()
        st.markdown("### About")
        st.info(
            "**Created by:** J. Pacocha\n\n"
            "**Purpose:** A privacy-focused tool to merge PDFs locally without external uploads.\n\n"
            "• [🌐 Website](https://jakubpacocha.com)\n\n • [🐙 GitHub](https://github.com/JPacoch)\n\n • [💼 LinkedIn](https://linkedin.com/in/jakubpacocha)"
        )

    uploaded_files = st.file_uploader(
        "Drag and drop PDFs here",
        type="pdf",
        accept_multiple_files=True,
    )

    st.session_state.setdefault("file_order", [])      
    st.session_state.setdefault("file_map", {})        
    st.session_state.setdefault("file_meta", {})       
    st.session_state.setdefault("range_inputs", {})    
    st.session_state.setdefault("merged_pdf_bytes", None)
    st.session_state.setdefault("last_upload_signature", "")

    if not uploaded_files:
        st.info("Upload at least 2 PDFs to merge.")
        return

    signature = "|".join(sorted([build_file_id(f) for f in uploaded_files]))
    uploads_changed = signature != st.session_state["last_upload_signature"]

    if uploads_changed:
        st.session_state["last_upload_signature"] = signature
        st.session_state["merged_pdf_bytes"] = None

        file_map: Dict[str, any] = {}
        file_meta: Dict[str, FileMeta] = {}
        for f in uploaded_files:
            fid = build_file_id(f)
            file_map[fid] = f

            try:
                reader = PdfReader(f)
                num_pages = len(reader.pages)
            except Exception:
                num_pages = 0

            file_meta[fid] = FileMeta(
                file_id=fid,
                name=f.name,
                size=f.size,
                num_pages=num_pages,
            )

            st.session_state["range_inputs"].setdefault(fid, "")
        fids = [build_file_id(f) for f in uploaded_files]

        st.session_state["file_map"] = file_map
        st.session_state["file_meta"] = file_meta
        st.session_state["file_order"] = fids

    order_fids: List[str] = st.session_state["file_order"]
    meta: Dict[str, FileMeta] = st.session_state["file_meta"]

    order_fids = [fid for fid in order_fids if fid in meta]
    st.session_state["file_order"] = order_fids

    st.subheader("1) Order your files")

    current_names = [meta[fid].name for fid in order_fids]
    new_names = try_sortables(current_names)

    if new_names is None:
        st.caption("Reorder with buttons (install `streamlit-sortables` for drag & drop).")
        for idx, fid in enumerate(order_fids):
            m = meta[fid]
            row = st.container(border=True)
            cols = row.columns([0.08, 0.62, 0.15, 0.15])

            cols[0].markdown(f"**{idx+1}.**")
            cols[1].markdown(f"**{m.name}**  \n{m.num_pages} pages • {human_size(m.size)}")

            up_disabled = idx == 0
            down_disabled = idx == len(order_fids) - 1

            if cols[2].button("⬆️", key=f"up_{fid}", disabled=up_disabled, use_container_width=True):
                order_fids[idx - 1], order_fids[idx] = order_fids[idx], order_fids[idx - 1]
                st.session_state["file_order"] = order_fids
                st.session_state["merged_pdf_bytes"] = None
                st.rerun()

            if cols[3].button("⬇️", key=f"down_{fid}", disabled=down_disabled, use_container_width=True):
                order_fids[idx + 1], order_fids[idx] = order_fids[idx], order_fids[idx + 1]
                st.session_state["file_order"] = order_fids
                st.session_state["merged_pdf_bytes"] = None
                st.rerun()
    else:
        name_to_fids: Dict[str, List[str]] = {}
        for fid in order_fids:
            name_to_fids.setdefault(meta[fid].name, []).append(fid)

        new_order: List[str] = []
        for nm in new_names:
            if nm in name_to_fids and name_to_fids[nm]:
                new_order.append(name_to_fids[nm].pop(0))

        if len(new_order) == len(order_fids) and new_order != order_fids:
            st.session_state["file_order"] = new_order
            st.session_state["merged_pdf_bytes"] = None
            order_fids = new_order

    st.subheader("2) Review files")
    header = st.columns([0.10, 0.44, 0.16, 0.15, 0.15])
    header[0].markdown("**#**")
    header[1].markdown("**Filename**")
    header[2].markdown("**Pages**")
    header[3].markdown("**Size**")
    header[4].markdown("**Selected**")

    range_errors: Dict[str, str] = {}
    selected_pages_counts: Dict[str, int] = {}

    for idx, fid in enumerate(order_fids):
        m = meta[fid]
        row = st.columns([0.10, 0.44, 0.16, 0.15, 0.15], vertical_alignment="center")

        row[0].write(str(idx + 1))
        row[1].write(m.name)
        row[2].write(str(m.num_pages))
        row[3].write(human_size(m.size))

        if m.num_pages <= 0:
            range_errors[fid] = "Could not read page count (file might be corrupted or unsupported)."
            row[4].write("—")
            continue

        if merge_mode == "All pages":
            selected_pages_counts[fid] = m.num_pages
            row[4].write(f"{m.num_pages}")
        else:
            default_val = st.session_state["range_inputs"].get(fid, "")
            with st.container():
                cols = st.columns([0.10, 0.44, 0.46])
                cols[0].write("")  # spacer
                cols[1].caption("Pages (e.g. 1-3,5)")
                new_val = cols[2].text_input(
                    label="",
                    value=default_val,
                    key=f"range_{fid}",
                    placeholder="leave empty for all pages",
                )
            st.session_state["range_inputs"][fid] = new_val

            indices, err = parse_page_ranges(new_val, m.num_pages)
            if err:
                range_errors[fid] = err
                selected_pages_counts[fid] = 0
                row[4].write("0")
            else:
                selected_pages_counts[fid] = len(indices)
                row[4].write(str(len(indices)))

    total_selected_pages = sum(selected_pages_counts.values())
    st.markdown(f"**Total pages to merge:** {total_selected_pages}")

    if range_errors:
        with st.expander("⚠️ Fix issues before merging", expanded=True):
            for fid, msg in range_errors.items():
                st.error(f"{meta[fid].name}: {msg}")

    st.subheader("3) Merge")
    can_merge = len(order_fids) >= 2 and not range_errors and total_selected_pages > 0

    merge_col1, merge_col2 = st.columns([0.6, 0.4], vertical_alignment="center")
    merge_clicked = merge_col1.button("Merge PDFs", type="primary", disabled=not can_merge, use_container_width=True)

    if merge_clicked:
        writer = PdfWriter()
        progress = st.progress(0)
        status = st.status("Merging PDFs…", expanded=True)

        try:
            total_files = len(order_fids)
            for i, fid in enumerate(order_fids, start=1):
                f = st.session_state["file_map"][fid]
                m = meta[fid]

                status.write(f"Adding: **{m.name}**")
                reader = PdfReader(f)

                if merge_mode == "All pages":
                    for page in reader.pages:
                        writer.add_page(page)
                else:
                    range_str = st.session_state["range_inputs"].get(fid, "")
                    indices, err = parse_page_ranges(range_str, len(reader.pages))
                    if err:
                        raise ValueError(f"{m.name}: {err}")
                    for pidx in indices:
                        writer.add_page(reader.pages[pidx])

                progress.progress(int(i / total_files * 100))

            output = BytesIO()
            writer.write(output)
            output.seek(0)

            st.session_state["merged_pdf_bytes"] = output.getvalue()
            status.update(label="✅ Merge complete", state="complete", expanded=False)
            st.toast("Merged successfully!")

        except Exception as e:
            status.update(label="❌ Merge failed", state="error", expanded=True)
            st.error(f"An error occurred: {e}")
            st.session_state["merged_pdf_bytes"] = None
        finally:
            try:
                writer.close()
            except Exception:
                pass

    merged_bytes = st.session_state.get("merged_pdf_bytes")
    if merged_bytes:
        merge_col2.download_button(
            label="Download Merged PDF",
            data=merged_bytes,
            file_name=output_name,
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        merge_col2.button("Download Merged PDF", disabled=True, use_container_width=True)

if __name__ == "__main__":
    main()
