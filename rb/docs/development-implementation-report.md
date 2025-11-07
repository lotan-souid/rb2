# דו"ח יישום – מחלקת פיתוח (Development)

מסמך זה מסכם את השינויים שבוצעו בקוד, מסביר את הטפסים, השדות שהתווספו או עודכנו, הלוגיקה העסקית וסדר העבודה בפועל.

---

## סקירה קצרה
- מטרת היישום: ניהול פרויקט פיתוח תשתיות עבור תב"ע (Plan) מאושרת, כולל שלבים, סעיפים, ועדות, חישוב מחיר פיתוח למ"ר, הקצאה למגרשים ומעקב התקדמות.
- תוספות אחרונות: הגדרת רשימת מגרשי הפרויקט (Development Project Lots) לצורך חישוב מדויק ועל מניעת כפילויות, ותיעוד פרויקטי תשתיות על (Regional Infrastructure Project) שאינם מחויבים דרך המגרשים.

---

## מה שונה בקוד
- DocTypes חדשים:
  - `Development Project Lot` – טבלת משנה שמחזיקה את המגרשים הרלוונטיים לפרויקט (כולל fetch לשדות plan/area וכו').
  - `Regional Infrastructure Project` + `Regional Infrastructure Project Link` – ישות על לקישור מספר פרויקטי פיתוח תחת פרויקט תשתיות על.
- Development Project מורחב:
  - טבלת `development_project_lots` עם אימות שמונע שיבוץ אותו מגרש בשני פרויקטים.
  - חישובי המחיר למ"ר והקצאות נשענים כעת על רשימת המגרשים בפועל, כולל ניקוי הקצאות ישנות והסנכרון לשדות `Lot`.
- קוד הדמו/seed עודכן ליצירת רשומות בטבלת המגרשים החדשה ולהפעלה של הקצאות בהתאם (קבצים `rb/demo/seed_development.py` ו־`rb/demo/seed_dummy.py`).
- מסמכי האפיון (`docs/development/development-spec.md`, מסמך זה) הורחבו כדי לשקף את שיטת העבודה המעודכנת.

---

## טפסים ושדות שנוספו/שונתה הגדרה

### Development Project – פרויקט פיתוח
- שדות חדשים/מורחבים:
  - מקור חישוב: `calculation_source` (Planned | Approved | Actual | ManualAdjustment)
  - מחיר למ"ר: `dev_price_per_sqm` (חישובי/נעול)
  - נעילת מחיר: `price_locked` (Check), `price_lock_date` (Date, לקריאה בלבד), `price_lock_reason` (Small Text)
  - היסטוריית מחיר: `price_history` (Table → Development Price History)
  - עלות להקצאה: `allocatable_total_cost` (Currency) – בסיס לחישוב המחיר למ"ר בעת מקור Approved/Manual
  - מגרשי פרויקט: `development_project_lots` (Table → Development Project Lot) – קובע את רשימת המגרשים לחיוב.

### Development Price History – היסטוריית מחיר למ"ר (טבלת משנה)
- שדות:
  - תאריך שינוי: `change_date` (Date)
  - מחיר למ"ר: `price_per_sqm` (Currency)
  - מקור חישוב: `calculation_source` (Select)
  - נעול: `locked` (Check)
  - הערה: `note` (Small Text)
- קבצים:
  - JSON: `frappe-bench/apps/rb/rb/development/doctype/development_price_history/development_price_history.json`
  - Controller: `frappe-bench/apps/rb/rb/development/doctype/development_price_history/development_price_history.py`

### Lot – מגרש (Planning)
- שדות שנוספו/להצגה:
  - לחיוב: `chargeable` (Check) – האם נכלל בסך השטח לחישוב מחיר למ"ר
  - פרויקט קשור: `related_project` (Link → Development Project, לקריאה בלבד)
  - מחיר מ"ר פיתוח: `dev_price_per_sqm` (Currency, לקריאה בלבד)
  - עלות פיתוח מוקצית: `allocated_dev_cost` (Currency, לקריאה בלבד)
  - סטטוס פיתוח: `lot_development_status` (Select: NotStarted | InProgress | Completed, נגזר)
- קובץ JSON: `frappe-bench/apps/rb/rb/planning/doctype/lot/lot.json`

### Development Project Lot – טבלת מגרשי פרויקט
- שדות:
  - `lot` (Link → Lot, reqd) + שדות fetch לקריאה בלבד (`plan`, `lot_number`, `area_sqm`, `housing_units`, `chargeable`, `development_status`).
  - `notes` לסימון פרטים מיוחדים (לדוגמה שכונה/שלב).
- קבצים:
  - JSON: `frappe-bench/apps/rb/rb/development/doctype/development_project_lot/development_project_lot.json`
  - Controller: `frappe-bench/apps/rb/rb/development/doctype/development_project_lot/development_project_lot.py`

### Regional Infrastructure Project – פרויקט תשתיות על
- שדות עיקריים: `infrastructure_project_name`, `funding_source`, `status`, `total_estimate_cost`, `total_actual_cost`, שדה טבלה `linked_projects` (Regional Infrastructure Project Link) לקישור פרויקטי פיתוח.
- קבצים:
  - JSON: `frappe-bench/apps/rb/rb/development/doctype/regional_infrastructure_project/regional_infrastructure_project.json`
  - Controller: `frappe-bench/apps/rb/rb/development/doctype/regional_infrastructure_project/regional_infrastructure_project.py`
  - טבלת קישור: `regional_infrastructure_project_link` (JSON+PY) לאחסון הפרויקטים המשויכים.

### Development Stage / Item / Committee Review / Stage Progress Update / Cost Allocation
- מבנה נשמר כפי שהוגדר, עם שילוב בלוגיקה של הפרויקט (ראו להלן).

---

## לוגיקה עסקית מרכזית (בקוד)
- קובץ: `frappe-bench/apps/rb/rb/development/doctype/development_project/development_project.py`

- חישוב עלויות פרויקט:
  - סכימה של `planned_cost` ו־`actual_cost` מסעיפים (Items) לשדות סיכום בפרויקט.
  - `allocatable_total_cost` נבחר לפי `calculation_source`:
    - Approved → משתמש בערך ידני/מאושר (`allocatable_total_cost`)
    - Planned → סכום מתוכנן
    - Actual → סכום בפועל
    - ManualAdjustment → שומר ערך קיים; לא מחושב אוטומטית

- מחיר למ"ר (`dev_price_per_sqm`):
  - חישוב: `allocatable_total_cost / Σ area_sqm` של המגרשים שנבחרו בטבלת `Development Project Lots` עם `chargeable=1`.
  - כש־`price_locked=1` המחיר לא יחושב מחדש (נשמר קיים).
  - רישום היסטוריה: בעת שינוי מחיר, נעילה/פתיחה – נרשמת שורה בטבלת `price_history` עם תאריך, מקור ונעילה.
  - אימותים: לא ניתן להוסיף Lot שאינו Chargeable, שאינו בתוכנית המוצהרת או שכבר משויך לפרויקט אחר.

- ניהול שלבים:
  - יצירת שלבי ברירת מחדל אם חסרים: StageA, StageB, Final.
  - עדכון סכומי שלב מתוך סעיפים.

- הקצאת עלויות למגרשים (`recalculate_cost_allocation`):
  - פועלת רק על רשימת המגרשים שבטבלת הפרויקט (Chargeable=1).
  - לכל Lot: `allocated_cost = area_sqm × dev_price_per_sqm`, יצירת/עדכון `Development Cost Allocation`, ודילוג על רשומות נעולות.
  - הסרה של מגרש מהטבלה תנקה את שדות העלות ב־Lot ותמחק הקצאות לא נעולות עבורו.
  - השתקפות בטופס Lot: עדכון `related_project`, `dev_price_per_sqm`, `allocated_dev_cost`, וסטטוס פיתוח.

- פעולות נעילה/פתיחה:
  - `lock_price_per_sqm(reason)` – מסמן נעילה, קובע תאריך/סיבה, מוסיף שורת היסטוריה.
  - `unlock_price_per_sqm(reason)` – פותח נעילה ומוסיף היסטוריה.

- Stage Progress Update:
  - אימות אחוזי התקדמות 0–100 ועדכון אחוז בשלב על בסיס עדכון אחרון (בקובץ `stage_progress_update.py`).
- Regional Infrastructure Project:
  - טופס תיעודי בלבד; מאפשר קישור מספר Development Projects ותיוג מקור מימון/סטטוס אזורי ללא השפעה על חישובי המגרשים.

---

## סדר עבודה מומלץ (Flow)
1) תכנון ואישור תב"ע (Plan)
   - יצירת Plan ועדכון סטטוס ל־Approved.

2) יצירת פרויקט פיתוח (Development Project)
   - יצירת שלבים וסעיפים; הזנת עלויות מתוכננות.
   - בחירת מגרשים בטבלת `Development Project Lots` (ניתן לבחור רק מתוך התוכניות שהוגדרו בשדות Plan/Participating Plans).

3) ועדה (Committee Review)
   - קביעת סטטוס הוועדה ל־Approved והזנת `approved_allocatable_cost` (אם רלוונטי).

4) חישוב מחיר למ"ר
   - בחירת `calculation_source` וקביעת `allocatable_total_cost` בהתאם.
   - שמירה/חישוב `dev_price_per_sqm` (אוטומטי אם לא נעול).
   - אופציונלי: `lock_price_per_sqm` לאחר החלטת ועדה/חוזים.

5) הקצאת עלויות למגרשים
   - הפעלה: `recalculate_cost_allocation` מהפרויקט (פועל רק על המגרשים שנבחרו).
   - עדכון שדות במגרשים: `related_project`, `dev_price_per_sqm`, `allocated_dev_cost`, וסטטוס פיתוח.

6) התחלת ביצוע ומעקב
   - מעבר פרויקט ל־InExecution.
   - עדכון התקדמות בשלבים (Stage Progress Update) ועלויות בפועל בסעיפים.

7) סגירת פרויקט
   - עם השלמת כל השלבים, סטטוס פרויקט → Completed; סטטוסי מגרשים → Completed.

8) (אופציונלי) פרויקט תשתיות על
   - יצירת `Regional Infrastructure Project` לצורך תיעוד מקור המימון וקישור מספר פרויקטי פיתוח תחת מעטפת אחת.

---

## הערות תפעול ופתרון תקלות
- לאחר עדכוני מודלים/פיקסצ'רים:
  - `bench --site rb.localhost migrate`
  - `bench --site rb.localhost clear-cache`
- אם מופיעה שגיאת יבוא DocType (ImportError): ודא שקיים קובץ `*.py` תואם לתיקיית ה־DocType.
- אם מיגרציה נכשלת על Fixtures: ודא שלכל רשומה קיים `name` ושה־JSON הוא מערך של אובייקטים.

---

## קישורים לקבצים רלוונטיים
- בקרי DocTypes (מפתח):
  - `frappe-bench/apps/rb/rb/development/doctype/development_project/development_project.py`
  - `frappe-bench/apps/rb/rb/development/doctype/development_project_lot/development_project_lot.py`
  - `frappe-bench/apps/rb/rb/development/doctype/development_stage/development_stage.py`
  - `frappe-bench/apps/rb/rb/development/doctype/stage_progress_update/stage_progress_update.py`
  - `frappe-bench/apps/rb/rb/development/doctype/development_price_history/development_price_history.py`
  - `frappe-bench/apps/rb/rb/development/doctype/regional_infrastructure_project/regional_infrastructure_project.py`
  - `frappe-bench/apps/rb/rb/development/doctype/regional_infrastructure_project_link/regional_infrastructure_project_link.py`
- הגדרות DocTypes (JSON):
  - `frappe-bench/apps/rb/rb/development/doctype/development_project/development_project.json`
  - `frappe-bench/apps/rb/rb/development/doctype/development_project_lot/development_project_lot.json`
  - `frappe-bench/apps/rb/rb/development/doctype/development_price_history/development_price_history.json`
  - `frappe-bench/apps/rb/rb/development/doctype/regional_infrastructure_project/regional_infrastructure_project.json`
  - `frappe-bench/apps/rb/rb/development/doctype/regional_infrastructure_project_link/regional_infrastructure_project_link.json`
  - `frappe-bench/apps/rb/rb/planning/doctype/lot/lot.json`
- מסמכי אפיון:
  - `docs/development/development-spec.md`
  - מסמך זה: `docs/development/development-implementation-report.md`
