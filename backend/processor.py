import os
import re
import pdfplumber
import pandas as pd
from typing import List, Dict

class FinancialProcessor:
    def __init__(self):
        # Weighted keywords for more intelligent classification
        self.bs_keywords = {
            "balance sheet": 10,
            "statement of financial position": 10,
            "assets": 3,
            "liabilities": 3,
            "equity": 3,
            "net assets": 5
        }
        self.pl_keywords = {
            "profit and loss": 10,
            "income statement": 10,
            "statement of operations": 10,
            "revenue": 3,
            "expenses": 3,
            "net income": 5,
            "ebitda": 5
        }
        
    def process_pdf(self, pdf_path: str, output_dir: str) -> str:
        extracted_data = self._extract_content(pdf_path)
        return self._save_to_excel(extracted_data, output_dir)
    
    def get_extracted_data(self, pdf_path: str) -> Dict[str, List[Dict[str, str]]]:
        extracted_data = self._extract_content(pdf_path)
        if extracted_data is None:
            return None
            
        return {
            sheet: df.to_dict(orient="records")
            for sheet, df in extracted_data.items()
        }
    
    def _classify_page(self, text: str) -> str:
        text_lower = text.lower()
        bs_score = sum(weight for kw, weight in self.bs_keywords.items() if kw in text_lower)
        pl_score = sum(weight for kw, weight in self.pl_keywords.items() if kw in text_lower)
        
        if bs_score > 8 and bs_score >= pl_score:
            return "BS"
        if pl_score > 8 and pl_score > bs_score:
            return "PL"
        return None

    def _extract_content(self, pdf_path: str) -> Dict[str, pd.DataFrame]:
        bs_data = []
        pl_data = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                category = self._classify_page(text)
                if not category:
                    continue
                
                # Intelligent table/text parsing
                page_data = self._parse_intelligent(page)
                
                if category == "BS":
                    bs_data.extend(page_data)
                elif category == "PL":
                    pl_data.extend(page_data)
        
        if not bs_data and not pl_data:
            return None
            
        # Group data and attempt to handle multiple columns (years) if present
        df_bs = self._finalize_dataframe(bs_data)
        df_pl = self._finalize_dataframe(pl_data)

        # Basic Accounting Validation (internal meta, could be used later)
        self._validate_accounting(df_bs)
        
        return {
            "Balance Sheet": df_bs,
            "Profit and Loss": df_pl
        }

    def _parse_intelligent(self, page) -> List[Dict]:
        extracted = []
        tables = page.extract_tables()
        
        # Detect year headers
        headers = []
        if tables:
            first_table = tables[0]
            if first_table and len(first_table[0]) > 1:
                potential_headers = [str(cell).strip() for cell in first_table[0]]
                headers = [h for h in potential_headers if re.search(r"(20\d{2})|Current|Prior", h)]

        if tables:
            for table in tables:
                for row in table:
                    if not row or len(row) < 2: continue
                    desc = str(row[0]).strip()
                    if not desc or len(desc) < 3: continue
                    
                    # Try to find the values
                    for i in range(1, len(row)):
                        val = str(row[i]).strip()
                        if self._is_numeric(val):
                            year = headers[i-1] if len(headers) >= i else "Latest"
                            extracted.append({"Description": desc, "Value": val, "Year": year})
                            # We collect all values, but _finalize_dataframe will pick the best
        
        if not extracted:
            text = page.extract_text()
            regex = r"([A-Za-z\s]{3,})\s+([\d,.-]+\d{2})"
            matches = re.finditer(regex, text)
            for match in matches:
                extracted.append({"Description": match.group(1).strip(), "Value": match.group(2).strip(), "Year": "Latest"})
                    
        return extracted

    def _finalize_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        if not data:
            return pd.DataFrame(columns=["Description", "Value"])
        df = pd.DataFrame(data)
        # Prioritize 'Latest' or highest year
        if 'Year' in df.columns:
            df['YearOrder'] = df['Year'].apply(lambda x: int(x) if re.match(r"20\d{2}", str(x)) else (9999 if str(x).lower() == 'latest' else 0))
            df = df.sort_values(by='YearOrder', ascending=False)
            
        df = df.drop_duplicates(subset=["Description"])
        return df[["Description", "Value"]]

    def _validate_accounting(self, df: pd.DataFrame) -> Dict:
        # Simple A = L + E check logic
        try:
            assets = self._sum_by_desc(df, ["total assets", "total non-current assets", "total current assets"])
            liabilities = self._sum_by_desc(df, ["total liabilities", "total equity", "liabilities and equity"])
            return {"balanced": abs(assets - liabilities) < 10.0} # Small margin for rounding
        except:
            return {"balanced": False}

    def _sum_by_desc(self, df: pd.DataFrame, keywords: List[str]) -> float:
        mask = df['Description'].str.lower().str.contains('|'.join(keywords))
        vals = df[mask]['Value'].apply(lambda x: float(str(x).replace(',', '').replace('(', '-').replace(')', '')) if self._is_numeric(x) else 0)
        return vals.sum()

    def _is_numeric(self, s: str) -> bool:
        if not s: return False
        s = s.replace(",", "").replace("-", "").replace("(", "").replace(")", "").strip()
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _save_to_excel(self, data_dict: Dict[str, pd.DataFrame], output_dir: str) -> str:
        filename = "Financial_Statement_Extracted.xlsx"
        output_path = os.path.join(output_dir, filename)
        
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for sheet_name, df in data_dict.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    pd.DataFrame(columns=["Description", "Value"]).to_excel(writer, sheet_name=sheet_name, index=False)
                    
        return output_path
