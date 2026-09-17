# Stage 3 — Exploratory Data Analysis (Business Perspective)

## Patient Demographics
- Gender split: {'Male': 27449, 'Female': 27411}
- Age range: 13–89, mean 51.5
- Most common blood type: A-
- Largest age group: Senior (66+)

## Medical Conditions
- Disease frequency (near-uniform by design): {'Arthritis': 9207, 'Diabetes': 9197, 'Hypertension': 9131, 'Obesity': 9127, 'Cancer': 9121, 'Asthma': 9077}
- Condition with longest avg stay: Asthma (15.7 days)
- Condition with highest avg billing: Obesity

## Hospital Operations
- Admissions are spread across 39,815 distinct hospital names (7,789 with >1 admission)
- Peak admission months: ['August', 'January', 'July']
- Average length of stay: 15.50 days (90th pct: 28 days)
- Admission type mix: {'Elective': 18437, 'Urgent': 18353, 'Emergency': 18070}

## Financial
- Total billing across all admissions: $1,404,121,601
- Average billing per admission: $25,594.63
- Correlation between Length of Stay and Billing Amount: -0.0048 (effectively no linear relationship — billing looks independent of stay length in this synthetic dataset)
- Highest-revenue medical condition: Diabetes
- Insurance billing spread across providers is nearly even: {'Aetna': 276516742.22, 'Blue Cross': 280416694.18, 'Cigna': 284346461.15, 'Medicare': 282921171.9, 'Unitedhealthcare': 279920531.85}

## Clinical
- Test result distribution: {'Abnormal': 18399, 'Normal': 18302, 'Inconclusive': 18159} — classes are near-balanced
- No strong association observed between Medical Condition and Test Results (near-uniform crosstab), consistent with this being a synthetic dataset without embedded clinical causality.
