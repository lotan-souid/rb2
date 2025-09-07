# דוגמאות Dummy Data לפי טפסים (להכנה לנתוני בדיקות)

מטרת המסמך: לתת דוגמאות ערכים לכל טופס כדי ליישר ציפיות לגבי מבנה/סוגי נתונים. ערכו כאן שמות שדות וערכים לפי הטפסים בפועל אצלכם; אשאב מכאן להכנת סקריפט זריעת נתונים (seed).

הפורמט לדוגמאות: אוסף רשומות בפורמט JSON‑like. ניתן להפוך בקלות ל־fixtures או סקריפט Insert.

הערות כלליות
- טלפונים בפורמט: ###-###-####
- תעודת זהות: 9 ספרות
- תאריכים: YYYY-MM-DD

—

## Tribe (שבט)
```json
{
  "doctype": "Tribe",
  "records": [
    {"tribe_name": "שמעון"},
    {"tribe_name": "לוי"},
    {"tribe_name": "נפתלי"},
    {"tribe_name": "יהודה"},
    {"tribe_name": "יששכר"},
    {"tribe_name": "זבולון"},
    {"tribe_name": "דן"},
    {"tribe_name": "גד"},
    {"tribe_name": "אשר"},
    {"tribe_name": "ראובן"},
    {"tribe_name": "בנימין"},
    {"tribe_name": "יוסף"}
  ]
}
```

## Evacuee (מפונה)
```json
{
  "doctype": "Evacuee",
  "records": [
    {"full_name": "בראד פיט", "id_number": "123456782", "phone": "052-123-4567", "email": "brad.pit@example.com"},
    {"full_name": "אנג'לינה ג'ולי", "id_number": "234567891", "phone": "054-222-3344"},
    {"full_name": "טום קרוז", "id_number": "345678912", "phone": "050-987-6543", "email": "tom.cruise@example.com"},
    {"full_name": "סנדרה בולוק", "id_number": "456789123", "phone": "053-111-2222"},
    {"full_name": "ג'ניפר לורנס", "id_number": "567891234", "phone": "055-876-5432", "email": "j.law@example.com"},
    {"full_name": "קיאנו ריבס", "id_number": "678912345", "phone": "052-765-4321"},
    {"full_name": "מריל סטריפ", "id_number": "789123456", "phone": "058-333-2211", "email": "meryl@example.com"},
    {"full_name": "דנזל וושינגטון", "id_number": "891234567", "phone": "052-444-7788"},
    {"full_name": "רוברט דאוני ג'וניור", "id_number": "912345678", "phone": "050-555-6677"},
    {"full_name": "נטלי פורטמן", "id_number": "135792468", "phone": "054-999-8888", "email": "n.portman@example.com"}
  ]
}
```

## Employee (עובד)
```json
{
  "doctype": "Employee",
  "records": [
    {"employee_name": "עומר אדם", "designation": "מנהל מרחב", "department": "אגף הסדרה", "mobile_no": "052-700-1111", "email_id": "omer.adam@example.com"},
    {"employee_name": "אייל גולן", "designation": "מנהל אגף", "department": "אגף הנהלה", "mobile_no": "052-700-2222"},
    {"employee_name": "שירי מימון", "designation": "איש אגף פיתוח", "department": "אגף פיתוח", "mobile_no": "052-700-3333"},
    {"employee_name": "שלמה ארצי", "designation": "איש GIS", "department": "אגף תכנון", "mobile_no": "052-700-4444"},
    {"employee_name": "נינט טייב", "designation": "רכז משא ומתן", "department": "אגף הסדרה", "mobile_no": "052-700-5555"},
    {"employee_name": "מרגלית צנעני", "designation": "איש אגף תכנון", "department": "אגף תכנון", "mobile_no": "052-700-6666"},
    {"employee_name": "רביד פלוטניק", "designation": "איש לוגיסטיקה", "department": "אגף כספים", "mobile_no": "052-700-7777"},
    {"employee_name": "נועה קירל", "designation": "רכז משא ומתן", "department": "אגף הסדרה", "mobile_no": "052-700-8888"}
  ]
}
```

## Designation (תפקיד)
```json
{
  "doctype": "Designation",
  "records": [
    {"designation_name": "רכז משא ומתן"},
    {"designation_name": "מנהל מרחב"},
    {"designation_name": "איש GIS"},
    {"designation_name": "מנהל אגף"},
    {"designation_name": "איש לוגיסטיקה"},
    {"designation_name": "איש אגף תכנון"},
    {"designation_name": "איש אגף פיתוח"}
  ]
}
```

## Department (אגף)
```json
{
  "doctype": "Department",
  "records": [
    {"department_name": "אגף פיתוח"},
    {"department_name": "אגף הסדרה"},
    {"department_name": "אגף תכנון"},
    {"department_name": "אגף הנהלה"},
    {"department_name": "אגף כספים"}
  ]
}
```

## Sector (אזור)
```json
{
  "doctype": "Sector",
  "records": [
    {"sector_name": "גליל עליון", "coordinator": "נינט טייב"},
    {"sector_name": "שרון דרומי", "coordinator": "נועה קירל"},
    {"sector_name": "עמק יזרעאל", "coordinator": "נינט טייב"},
    {"sector_name": "שפלת יהודה", "coordinator": "נועה קירל"},
    {"sector_name": "נגב מערבי", "coordinator": "נינט טייב"},
    {"sector_name": "ערבה תיכונה", "coordinator": "נועה קירל"}
  ]
}
```

## Region (מרחב)
```json
{
  "doctype": "Region",
  "records": [
    {"region_name": "מרחב צפון", "region_manager": "עומר אדם"},
    {"region_name": "מרחב מרכז", "region_manager": "שירי מימון"},
    {"region_name": "מרחב דרום", "region_manager": "אייל גולן"}
  ]
}
```

## Cluster (אשכול/שבט)
```json
{
  "doctype": "Cluster",
  "records": [
    {"cluster_name": "כהן",   "tribe": "לוי",   "sector": "גליל עליון", "agreement_type": "Arrangement File", "established_date": "1984-06-12"},
    {"cluster_name": "לוי",    "tribe": "יהודה", "sector": "שרון דרומי", "agreement_type": "None",             "established_date": "1992-03-01"},
    {"cluster_name": "מזרחי",  "tribe": "נפתלי", "sector": "נגב מערבי",   "agreement_type": "Arrangement File", "established_date": "1979-11-22"},
    {"cluster_name": "חדד",    "tribe": "בנימין","sector": "עמק יזרעאל", "agreement_type": "None",             "established_date": "2001-07-15"},
    {"cluster_name": "פרץ",    "tribe": "דן",    "sector": "שפלת יהודה", "agreement_type": "Arrangement File", "established_date": "1995-02-10"}
  ]
}
```

## Planning Committee (ועדת תכנון)
```json
{
  "doctype": "Planning Committee",
  "records": [
    {"committee_name": "ועדת תכנון מרחבית הגליל"},
    {"committee_name": "ועדת תכנון נגב"},
    {"committee_name": "ועדת תכנון מרכז"}
  ]
}
```

## Planning Zone (אזור תכנון)
```json
{
  "doctype": "Planning Zone",
  "records": [
    {"planning_zone_name": "אזור תכנון בקעת הירדן"},
    {"planning_zone_name": "אזור תכנון שרון"},
    {"planning_zone_name": "אזור תכנון גולן"},
    {"planning_zone_name": "אזור תכנון שומרון"}
  ]
}
```

## Plan (תב"ע)
```json
{
  "doctype": "Plan",
  "records": [
    {"plan_number": "101-000123", "plan_name": "תב""ע הרחבת כביש 90 - צפון", "planning_committee": "ועדת תכנון מרחבית הגליל", "planning_zone": "אזור תכנון גולן", "approval_date": "2023-05-12"},
    {"plan_number": "204-012345", "plan_name": "תב""ע שכונת מגורים נווה צוף", "planning_committee": "ועדת תכנון מרכז",       "planning_zone": "אזור תכנון שרון", "approval_date": "2022-11-02"},
    {"plan_number": "315-100200", "plan_name": "תב""ע פארק תעשייה נגב צפון",   "planning_committee": "ועדת תכנון נגב",         "planning_zone": "אזור תכנון שומרון", "approval_date": "2021-03-27"}
  ]
}
```

## Lot (מגרש)
```json
{
  "doctype": "Lot",
  "records": [
    {"lot_number": "1",  "plan": "101-000123", "area_sqm": 450,  "chargeable": 1},
    {"lot_number": "2",  "plan": "101-000123", "area_sqm": 600,  "chargeable": 1},
    {"lot_number": "12", "plan": "204-012345", "area_sqm": 320,  "chargeable": 1},
    {"lot_number": "13", "plan": "204-012345", "area_sqm": 510,  "chargeable": 1},
    {"lot_number": "A1", "plan": "315-100200", "area_sqm": 1200, "chargeable": 1}
  ]
}
```

## Development Project (פרויקט פיתוח)
```json
{
  "doctype": "Development Project",
  "records": [
    {"plan": "101-000123", "development_project_name": "פיתוח כביש 90 צפון", "calculation_source": "Approved", "allocatable_total_cost": 3500000, "committee_status": "Pending"},
    {"plan": "204-012345", "development_project_name": "תשתיות שכונת נווה צוף", "calculation_source": "Planned",  "committee_status": "Pending"}
  ]
}
```

## Development Stage (שלב פיתוח)
```json
{
  "doctype": "Development Stage",
  "records": [
    {"development_project": "פיתוח כביש 90 צפון",   "stage_name": "StageA"},
    {"development_project": "פיתוח כביש 90 צפון",   "stage_name": "StageB"},
    {"development_project": "פיתוח כביש 90 צפון",   "stage_name": "Final"},
    {"development_project": "תשתיות שכונת נווה צוף", "stage_name": "StageA"},
    {"development_project": "תשתיות שכונת נווה צוף", "stage_name": "Final"}
  ]
}
```

## Development Item (סעיף פיתוח)
```json
{
  "doctype": "Development Items",
  "records": [
    {"item_name": "עבודות עפר",   "stage": "StageA", "category": "Earthworks", "quantity": 1000, "unit": "m3", "unit_cost": 50,  "item_status": "InTender"},
    {"item_name": "קו מים ראשי",  "stage": "StageA", "category": "Water",      "quantity": 800,  "unit": "m",  "unit_cost": 120, "item_status": "Planned"},
    {"item_name": "כביש גישה",     "stage": "StageB", "category": "Roads",      "quantity": 500,  "unit": "m",  "unit_cost": 300, "item_status": "Planned"},
    {"item_name": "תאורה היקפית", "stage": "Final",  "category": "Lighting",   "quantity": 80,   "unit": "unit","unit_cost": 900, "item_status": "Planned"}
  ]
}
```

## Committee Review (ועדה)
```json
{
  "doctype": "Development Committee Review",
  "records": [
    {"development_project": "פיתוח כביש 90 צפון",   "committee_status": "Approved",          "review_date": "2025-09-01", "approved_allocatable_cost": 3600000, "summary": "אישור תקציב לביצוע שלב א' וב'"},
    {"development_project": "תשתיות שכונת נווה צוף", "committee_status": "RevisionsRequired", "review_date": "2025-09-03", "summary": "נדרשים עדכוני פירוט לכמויות"}
  ]
}
```

## Stage Progress Update (עדכון התקדמות)
```json
{
  "doctype": "Stage Progress Update",
  "records": [
    {"development_stage": "StageA", "update_date": "2025-09-10", "progress_percent": 35, "notes": "סיום חפירה 30%"},
    {"development_stage": "StageB", "update_date": "2025-09-18", "progress_percent": 10}
  ]
}
```

## Development Cost Allocation (הקצאת עלויות)
```json
{
  "doctype": "Development Cost Allocation",
  "records": [
    {"development_project": "פיתוח כביש 90 צפון",   "lot": "1",  "calculation_source": "Approved", "calculation_date": "2025-09-12", "chargeable_area_sqm": 450,  "price_per_sqm": 1200, "allocated_cost": 540000},
    {"development_project": "פיתוח כביש 90 צפון",   "lot": "2",  "calculation_source": "Approved", "calculation_date": "2025-09-12", "chargeable_area_sqm": 600,  "price_per_sqm": 1200, "allocated_cost": 720000},
    {"development_project": "תשתיות שכונת נווה צוף", "lot": "12", "calculation_source": "Planned",  "calculation_date": "2025-09-12", "chargeable_area_sqm": 320,  "price_per_sqm": 950,  "allocated_cost": 304000}
  ]
}
```

—

הנחיות להתאמות לפני יצירת דאטה בפועל
- התאימו שמות שדות לערכים הקיימים בטפסים אצלכם (למשל `development_project_name` מול `project_name`, או `committee_status` וכו').
- קישורי Link חייבים להתאים לשמות האמיתיים במסד (לדוגמה `plan`, `lot`, `development_stage`).
- אם טפסים מסוימים אינם קיימים אצלכם (למשל Sector/Region/Cluster), השאירו את החלקים שלהם מסומנים כ‑N/A או מחקו לפני הזרעה.

לאחר עדכון המסמך אכין סקריפט זריעת נתונים (Python/bench execute) בהתאם.

