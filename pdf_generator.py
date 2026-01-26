from fpdf import FPDF
from fpdf.fonts import FontFace 
import pandas as pd
from datetime import datetime
import io

class PDFReport(FPDF):
    def __init__(self, company_name):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.company_name = company_name
        self.report_date = datetime.now().strftime("%d-%b-%Y")
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_fill_color(30, 60, 114) 
        self.rect(0, 0, 210, 20, 'F')
        self.set_y(5)
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, f"{self.company_name}", align='L', new_x="LMARGIN", new_y="NEXT")
        self.set_font('Helvetica', '', 10)
        self.cell(0, 5, f"Financial Analysis Report | Date: {self.report_date}", align='L')
        self.ln(10)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def add_section_title(self, title):
        self.ln(5)
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(30, 60, 114)
        self.cell(0, 8, title, border=0, fill=True, align='L', new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def add_dataframe_table(self, df):
        if df.empty:
            self.set_font('Helvetica', 'I', 10)
            self.cell(0, 10, "No Data Available")
            self.ln()
            return

        n_cols = len(df.columns)
        # Dynamic Column Widths
        if n_cols == 2:
             col_widths = [80, 50] 
             alignments = {"Metric": "L", df.columns[1]: "C"}
        elif n_cols > 0:
            metric_col_width = 50
            data_col_width = (190 - metric_col_width) / n_cols 
            col_widths = [metric_col_width] + [data_col_width] * n_cols
            alignments = None
        else:
            col_widths = None
            alignments = None

        self.set_font('Helvetica', '', 8)
        
        
        with self.table(
            borders_layout="ALL",
            cell_fill_color=(252, 252, 252),
            col_widths=col_widths,
            text_align="CENTER",
            line_height=6
        ) as table:
            
            # --- Header Row ---
            row = table.row()
            # Define Bold Style
            bold_style = FontFace(emphasis="BOLD")

            # Manually handle 'Metric' column header
            if "Metric" not in df.columns:
                row.cell("Metric", style=bold_style) 
            
            for col in df.columns:
                 row.cell(str(col), style=bold_style) 

            # --- Data Rows ---
            for index, data_row in df.iterrows():
                row = table.row()
                # Manually handle Index column
                if "Metric" not in df.columns:
                    row.cell(str(index), align="L")
                
                for i, val in enumerate(data_row):
                    align = "C"
                    if n_cols == 2 and i == 0: align = "L"
                    row.cell(str(val), align=align)
        
        self.ln(4)

    def add_image_chart(self, title, image_bytes):
        self.add_section_title(title)
        self.image(image_bytes, w=170)
        self.ln(5)

def create_pdf(company_name, data_dict):
    pdf = PDFReport(company_name)
    pdf.add_page()

    for section_name, content in data_dict.items():
        # Simple DataFrame
        if isinstance(content, pd.DataFrame):
             pdf.add_section_title(section_name)
             pdf.add_dataframe_table(content)
        
        # Dictionary (Sub-sections or Images)
        elif isinstance(content, dict):
            pdf.add_section_title(section_name)
            for sub_title, sub_content in content.items():
                
                
                if isinstance(sub_content, pd.DataFrame):
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 6, sub_title, new_x="LMARGIN", new_y="NEXT")
                    pdf.add_dataframe_table(sub_content)
                
                
                elif isinstance(sub_content, (bytes, io.BytesIO)):
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 6, sub_title, new_x="LMARGIN", new_y="NEXT")
                    pdf.image(sub_content, w=180)
                    pdf.ln(5)

    return bytes(pdf.output())