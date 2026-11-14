# british.py — Diabetic Medicine 규정(영국식 철자): 빌더가 원고·표·범례 문자열을 출력 직전에 변환한다(참고문헌 서지는 원문 유지).
import re
STEMS = ["standardiz", "harmoniz", "summariz", "characteriz", "categoriz", "recogniz", "emphasiz", "minimiz", "maximiz", "prioritiz", "utiliz", "organiz",
         "randomiz", "generaliz", "normaliz", "visualiz", "hospitaliz", "urbaniz", "stabiliz", "specializ", "realiz", "finaliz", "authoriz", "localiz", "conceptualiz", "operationaliz", "penaliz", "parameteriz", "criticiz", "jeopardiz", "mobiliz", "optimiz", "hypothesiz", "emphasiz", "apologiz", "memoriz"]
WORDS = {"analyze": "analyse", "analyzed": "analysed", "analyzes": "analyses", "analyzing": "analysing", "modeled": "modelled", "modeling": "modelling",
         "center": "centre", "centers": "centres", "centered": "centred", "neighbor": "neighbour", "neighbors": "neighbours", "neighborhood": "neighbourhood", "neighborhoods": "neighbourhoods",
         "behavior": "behaviour", "behaviors": "behaviours", "behavioral": "behavioural", "aging": "ageing", "color": "colour", "favor": "favour", "favorable": "favourable",
         "labeled": "labelled", "traveled": "travelled", "gray": "grey", "fiber": "fibre", "program": "programme", "programs": "programmes", "percent": "per cent",
         "hemoglobin": "haemoglobin", "glycemic": "glycaemic", "anemia": "anaemia", "fetal": "foetal", "pediatric": "paediatric", "edema": "oedema", "equaled": "equalled", "neighboring": "neighbouring", "modeler": "modeller", "acknowledgment": "acknowledgement", "acknowledgments": "acknowledgements", "judgment": "judgement"}
def brit(t):
    if not t: return t
    def stem(m):
        w = m.group(0); low = w.lower()
        for s in STEMS:
            if low.startswith(s):
                r = s[:-1] + "s" + low[len(s):]
                return r[0].upper() + r[1:] if w[0].isupper() else r
        return w
    t = re.sub(r"\b[A-Za-z]*iz(?:e|ed|es|ing|ation|ations|er|ers)\b", stem, t)
    def word(m):
        w = m.group(0); r = WORDS.get(w.lower())
        if r is None: return w
        return r[0].upper() + r[1:] if w[0].isupper() else r
    t = re.sub(r"\b[A-Za-z]+\b", word, t)
    return t.replace("World Health Organisation", "World Health Organization")   # 고유명사(WHO 공식 표기) 보호
if __name__ == "__main__":
    print(brit("Expected counts were standardized and harmonized; models were modeled with neighbors, centered covariates, aging behavior, glycemic outcomes, Standardization, size, prize."))
