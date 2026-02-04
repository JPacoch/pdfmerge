import re
from io import BytesIO
import streamlit as st
from pypdf import PdfWriter


def natural_sort_key(file_obj):
    """
    Sort helper that handles numbers in filenames naturally.
    Example: 1.pdf, 2.pdf, 10.pdf instead of 1.pdf, 10.pdf, 2.pdf
    """
    s = file_obj.name
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def main():
    st.set_page_config(page_title="PDF Merger", page_icon="📄")
    st.title("📄 PDF Merger Tool")
    st.write("Upload PDF files via your browser to merge them.")

    uploaded_files = st.file_uploader(
        "Drag and drop PDFs here",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files:
        # Sort files naturally by filename
        uploaded_files = sorted(uploaded_files, key=natural_sort_key)

        st.subheader("Selected Files (Sorted):")
        for f in uploaded_files:
            st.text(f"📄 {f.name}")

        if st.button("Merge PDFs"):
            merger = PdfWriter()
            try:
                for pdf in uploaded_files:
                    merger.append(pdf)

                output = BytesIO()
                merger.write(output)
                output.seek(0)

                st.success(f"✅ Successfully merged {len(uploaded_files)} PDFs")

                st.download_button(
                    label="Download Merged PDF",
                    data=output,
                    file_name="merged_document.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                merger.close()


if __name__ == "__main__":
    main()
