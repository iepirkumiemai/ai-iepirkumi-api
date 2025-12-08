import os
import json
from typing import List, Dict, Any
from pathlib import Path
from openai import OpenAI

from document_parser import DocumentParser, DocumentParserError


class AIComparisonEngine:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing.")

        self.client = OpenAI(api_key=api_key)

    # ============================================================
    # 1. Prasību sadalīšana punktos
    # ============================================================
    def split_requirements(self, text: str) -> List[str]:
        prompt = f"""
        Tu esi profesionāls publisko iepirkumu dokumentu analītiķis.

        Šeit ir iepirkuma prasību dokuments:

        ---------------------
        {text}
        ---------------------

        Uzdevums:
        - sadali prasības skaidros, numerētos punktos
        - viens punkts = viena prasība
        - saglabā secību un loģisko struktūru
        - neatkārto tekstu vairāk nekā nepieciešams

        Atgriez tikai sarakstu ar prasībām.
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        raw = response.choices[0].message.content
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        return lines

    # ============================================================
    # 2. Analīzes ģenerēšana pa punktiem
    # ============================================================
    def compare_requirements(
        self, 
        requirements: List[str], 
        candidate_text: str
    ) -> List[Dict[str, Any]]:

        req_list_json = json.dumps(requirements, ensure_ascii=False)

        prompt = f"""
        Tu esi starptautisks publisko iepirkumu eksperts.

        Prasību saraksts JSON formātā:
        {req_list_json}

        Kandidāta dokuments:
        ------------------------
        {candidate_text}
        ------------------------

        Uzdevums:
        1. Izvērtē katru prasību atsevišķi.
        2. Statusi:
           - "Atbilst"
           - "Daļēji atbilst"
           - "Neatbilst"
        3. Katram punktam pievieno īsu pamatojumu.
        4. Atgriez *tikai* validu JSON sarakstu:

        [
          {{
            "requirement": "...",
            "status": "...",
            "justification": "..."
          }}
        ]
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        raw_json = response.choices[0].message.content
        return json.loads(raw_json)

    # ============================================================
    # 3. Executive summary
    # ============================================================
    def generate_summary(self, results: List[Dict[str, Any]]) -> str:
        prompt = f"""
        Tu esi publisko iepirkumu analītiķis.

        Analīzes rezultāti:
        {json.dumps(results, ensure_ascii=False)}

        Sagatavo īsu, profesionālu kopsavilkumu (executive summary),
        maksimums 8 teikumi, bez sarakstiem.
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content

    # ============================================================
    # 4. HTML tabula WordPress priekšskatam
    # ============================================================
    def generate_html_table(self, results: List[Dict[str, Any]]) -> str:
        rows = []

        for item in results:
            rows.append(f"""
                <tr>
                    <td>{item['requirement']}</td>
                    <td>{item['status']}</td>
                    <td>{item['justification']}</td>
                </tr>
            """)

        return f"""
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>Prasība</th>
                <th>Atbilstība</th>
                <th>Pamatojums</th>
            </tr>
            {''.join(rows)}
        </table>
        """

    # ============================================================
    # 5. Pilnais analīzes process
    # ============================================================
    def analyze(self, req_path: Path, cand_path: Path) -> Dict[str, Any]:

        req_data = DocumentParser.extract(req_path)
        cand_data = DocumentParser.extract(cand_path)

        requirements = self.split_requirements(req_data["text"])
        comparison = self.compare_requirements(requirements, cand_data["text"])
        summary = self.generate_summary(comparison)
        table_html = self.generate_html_table(comparison)

        return {
            "summary": summary,
            "analysis": comparison,
            "table_html": table_html,
            "requirements_points": requirements
        }
