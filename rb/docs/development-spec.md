# מסמך אפיון – מחלקת פיתוח (Development)

מסמך זה מגדיר את הטפסים, המבנה והלוגיקה לעבודה עם תוכנית בניין עיר (תב"ע = Plan), מגרשים (Lot), ופרויקט פיתוח תשתיות (Development). המסמך מיועד למחלקת הפיתוח של האפליקציה.

## מטרות

- ניהול פרויקט פיתוח תשתיות עבור תב"ע מאושרת על־ידי מחלקת תכנון (Planning).
- תכנון מפורט לפי שלבים וסעיפים, כולל תקציב ועלויות בפועל.
- ועדה תוך־משרדית לאישור/דחייה/תיקונים של עלויות ותכולה.
- ביצוע, מעקב ובקרה על התקדמות ועלויות.
- הקצאת עלויות למגרשים לפי שטח (מחיר למ"ר) והצגתן בטופס המגרש.

---

## ישויות וקשרים (ER)

- Plan (תב"ע) ← 1—N → Lot (מגרשים)
- Plan ↔ N—N ↔ DevelopmentProject (פרויקט יכול לכסות מספר תוכניות באמצעות Participating Plans)
- DevelopmentProject ← 1—N → DevelopmentStage (שלבים: שלב א, שלב ב, גמר)
- DevelopmentStage ← 1—N → DevelopmentItem (סעיפי פיתוח)
- DevelopmentProject ← 1—N → CommitteeReview (דיוני ועדה)
- DevelopmentStage ← 1—N → StageProgressUpdate (עדכוני התקדמות)
- DevelopmentProject ← 1—N → DevelopmentProjectLot → 1—1 Lot
- DevelopmentProject ← 1—N → CostAllocation (הקצאת עלויות למגרשים שנבחרו)
- RegionalInfrastructureProject ← 1—N → Development Projects (באמצעות Regional Infrastructure Project Link)

**הערות:**
- Lot יחיד לא יכול להשתייך לשני פרויקטי פיתוח במקביל (עלות משויכת לפרויקט בודד).
- `CostAllocation` מחושב ברמת פרויקט ומשויך רק למגרשים שנמצאים ב־Development Project Lots.

---

## טפסים (Forms)

### 1) Plan – תוכנית בניין עיר (תב"ע)

**תיאור:** ניהול נתוני התוכנית, סטטוס האישור, גבולות וייעודים.

**פעולות עיקריות:** יצירת פרויקט פיתוח, ניווט לרשימת מגרשים, צפייה במחיר פיתוח למ"ר (מחושב מהפרויקט).

**שדות עיקריים:** ראה מילון שדות → Plan.

### 2) Lot – מגרש

**תיאור:** הצגת נתוני המגרש, ייעוד, שטח, סטטוס פיתוח ועלויות מוקצות.

**פעולות עיקריות:** צפייה בפילוח עלות פיתוח לפי שלבים/סעיפים, צפייה בסטטוס פיתוח, הדפסת דוח חיוב.

**נתונים מחושבים:** מחיר פיתוח למ"ר של הפרויקט, עלות מוקצית למגרש (שטח × מחיר למ"ר).

**שדות עיקריים:** ראה מילון שדות → Lot.

### 3) Development Project – פרויקט פיתוח

**תיאור:** ישות־על לתכנון מפורט, ביצוע, ועדות והקצאות עלויות.

**פעולות עיקריות:** הוספת שלבים וסעיפים, פתיחת ועדה, אישור/דחייה/תיקונים, חישוב הקצאות, מעבר לביצוע.

**שדות עיקריים:** ראה מילון שדות → DevelopmentProject.

**הערה:** כולל טבלת היסטוריית מחיר למ"ר (Development Price History) לצורך תיעוד ושחזור.
**מגרשים:** יש להוסיף את המגרשים הרלוונטיים בטבלת Development Project Lots; כל הלוגיקה הפיננסית נשענת על בחירה זו.

### 4) Development Stage – שלב פיתוח

**תיאור:** שלבים לוגיים של העבודה (לדוגמה: שלב א – עבודות עפר ותשתיות ראשיות; שלב ב – חיבורי תשתיות למגרשים; גמר – מדרכות, תאורה, גינון וכו').

**פעולות עיקריות:** הוספת/עריכת סעיפי פיתוח, עדכוני התקדמות, סימון השלמת שלב.

**שדות עיקריים:** ראה מילון שדות → DevelopmentStage.

### 5) Development Item – סעיף פיתוח

**תיאור:** פריט עבודה עם כמות, יחידה, עלות יחידה, עלות מתוכננת ובפועל, סטטוס.

**פעולות עיקריות:** ניהול מכרז/קבלן, עדכון סטטוס, רישום עלויות בפועל, הערות.

**שדות עיקריים:** ראה מילון שדות → DevelopmentItem.

### 6) Committee Review – ועדה תוך־משרדית

**תיאור:** דיון על עלויות, היתכנות ושלבים; אישור/דחייה/תיקונים לפרויקט.

**פעולות עיקריות:** פתיחת דיון, הזנת החלטות, קיבוע עלות מאושרת להקצאה.

**שדות עיקריים:** ראה מילון שדות → CommitteeReview.

### 7) Stage Progress Update – עדכון התקדמות שלב

**תיאור:** מעקב שוטף אחרי קצב ההתקדמות והוצאות בפועל.

**פעולות עיקריות:** הוספת עדכון, עדכון אחוז התקדמות, רישום הוצאה בפועל.

**שדות עיקריים:** ראה מילון שדות → StageProgressUpdate.

### 8) Cost Allocation – הקצאת עלויות

**תיאור:** חישוב והקצאת עלות פיתוח לכל מגרש על בסיס שטח.

**פעולות עיקריות:** הרצת חישוב, קיבוע מחיר למ"ר, הפקת דוחות חיוב.

**שדות עיקריים:** ראה מילון שדות → CostAllocation.

### 9) Development Price History – היסטוריית מחיר למ"ר

**תיאור:** טבלת משנה בפרויקט הפיתוח המתעדת שינויי מחיר למ"ר לאורך זמן, כולל מקור החישוב ונעילה.

**שימוש:** נרשמת אוטומטית בעת שינוי המחיר, נעילה/ביטול נעילה, או עדכון ידני בהרשאה.

**שדות עיקריים:** ראה מילון שדות → DevelopmentPriceHistory.

### 10) Development Project Lots – מגרשי פרויקט

**תיאור:** טבלת משנה בטופס פרויקט הפיתוח שמגדירה במפורש אילו מגרשים משתתפים בפרויקט וחייבים בעלויות.

**פעולות עיקריות:** בחירת מגרשים מהתוכניות המאושרות, בדיקה שהם Chargeable, הסרה/החלפה של מגרשים לפי תחומי אחריות.

**נתונים מחושבים:** שטח, יחידות דיור וסטטוס פיתוח נטענים אוטומטית מהמגרש לקריאה בלבד.

**שדות עיקריים:** ראה מילון שדות → DevelopmentProjectLot.

### 11) Regional Infrastructure Project – פרויקט תשתיות על

**תיאור:** ישות עליונה לתיעוד פרויקטי תשתיות מנקודת מבט אזורית (שאינם מחויבים דרך מגרשים), עם קישור למספר פרויקטי פיתוח.

**פעולות עיקריות:** מעקב אחרי מקור המימון, תקציב, סטטוס, וקישור הפרויקטים המקומיים שהפרויקט האזורי משרת.

**שדות עיקריים:** ראה מילון שדות → RegionalInfrastructureProject.

---

## סטטוסים וזרימת עבודה

### סטטוס Plan (תכנון)

```
טיוטה → נשלח → אושר | נדחה
Draft → Submitted → Approved | Rejected
```

רק Plan במצב Approved ניתן לפתוח עבורו DevelopmentProject לביצוע.

### סטטוס DevelopmentProject

```
טיוטה → בדיון ועדה → אושר | נדרשים תיקונים | נדחה → בביצוע → הושלם
Draft → UnderCommitteeReview → Approved | RevisionsRequired | Rejected → InExecution → Completed
```

מעבר ל־InExecution חסום ללא CommitteeReview במצב Approved.

### סטטוס DevelopmentStage

```
לא התחיל → בתהליך → הושלם | מושהה
NotStarted → InProgress → Completed | OnHold
```

שלב יהפוך `Completed` רק כאשר כל ה־DevelopmentItem בו `Completed`.

### סטטוס DevelopmentItem

```
מתוכנן → במכרז → בביצוע → הושלם | בוטל
Planned → InTender → InExecution → Completed | Canceled
```

### סטטוס פיתוח במגרש (לתצוגה ב־Lot)

נגזר ממצב הפרויקט והשלבים: `NotStarted | InProgress | Completed`

---

## לוגיקה עסקית וחישובים

### 1) תכנון מפורט והוועדה

- מחלקת הפיתוח יוצרת DevelopmentProject ל־Plan Approved, מוסיפה DevelopmentStage ו־DevelopmentItem עם עלות מתוכננת.
- מועבר ל־CommitteeReview: שינוי `committee_status` ל־Pending.
- החלטת הוועדה: **Approved** | **Rejected** | **RevisionsRequired**.
  - **Approved:** שדה `approved_allocatable_cost` יקובע לצורך הקצאה.
  - **RevisionsRequired:** חוזר ל־Draft עם דרישות תיקון.
  - **Rejected:** הפרויקט נעצר.

### 2) התחלת ביצוע וניהול התקדמות

- רק לאחר CommitteeReview=Approved ניתן להעביר את הפרויקט ל־InExecution.
- עדכוני התקדמות (StageProgressUpdate) מעדכנים `progress_percent` ברמת שלב ומסכמים ל־Project.
- עלויות בפועל נרשמות ב־DevelopmentItem או ב־StageProgressUpdate ומסוכמות ל־Stage ול־Project.

### 3) חישוב עלויות לפרויקט

- **עלות מתוכננת בפרויקט:** Σ `DevelopmentItem.planned_cost` בכל השלבים.
- **עלות בפועל בפרויקט:** Σ `DevelopmentItem.actual_cost` + Σ `StageProgressUpdate.actual_expense` (אם משתמשים בשניהם, יש להגדיר מקור אמת ולמנוע כפילות).
- **עלות להקצאה (allocatable_total_cost):**
  - ברירת מחדל: `CommitteeReview.approved_allocatable_cost` אם קיים; אחרת עלות מתוכננת/בפועל לפי הגדרה עסקית (`calculation_source`).

### 4) חישוב מחיר פיתוח למ"ר

- `Σ chargeable_area_sqm for Development Project Lots` = סך השטחים לחיוב של המגרשים שנבחרו בטבלה (Chargeable=1).
- `dev_price_per_sqm = allocatable_total_cost / Σ chargeable_area_sqm`.
- ניתן לקבע (`locked`) את המחיר למ"ר בנקודת זמן מוגדרת (לאחר אישור ועדה או לאחר חוזי קבלן) כדי למנוע תנודתיות.

### 5) הקצאת עלות לכל מגרש (CostAllocation)

לכל Lot שנמצא בטבלת Development Project Lots:
- `chargeable_area_sqm = Lot.area_sqm` (או שדה חלופי לפי מדיניות).
- `price_per_sqm = dev_price_per_sqm` (או ערך ידני כאשר `calculation_source = ManualAdjustment`).
- `allocated_cost = chargeable_area_sqm × price_per_sqm`.

שינוי ב־allocatable_total_cost או בשטחים מחייב ריצה מחדש של ההקצאה (אלא אם `locked=true`).

### 6) כללי אימות

- אי־אפשר להעביר Project ל־InExecution אם CommitteeReview ≠ Approved.
- אי־אפשר לסמן Stage כ־Completed אם קיימים Items שאינם Completed.
- `planned_cost` של Item = `quantity × unit_cost` (חישוב אוטומטי; ניתן לעדכון ידני רק בהרשאה).
- סכומי עלויות בפועל חייבים להיות ≥ 0; אחוז התקדמות 0–100.
- Lot לא יכול להיות משויך לשני פרויקטי פיתוח שונים; האימות מבוצע בעת שמירה של Development Project.

### 7) הצגה בטופס Lot

- `lot_development_status` נגזר אוטומטית: NotStarted (אין שלב פעיל), InProgress (קיים שלב פעיל), Completed (כל השלבים Completed).
- הצגת `dev_price_per_sqm` ו־`allocated_dev_cost` (מחושבים/מקובעים) כולל תאריך חישוב ומקור.

### 8) Regional Infrastructure Project

- מיועד לפרויקטי תשתיות על שאינם מגולגלים על המגרשים; העלויות ממומנות ממקור חיצוני (שדה `funding_source`).
- מאפשר לקשר מספר Development Projects תחת מעטפת תשתיתית אחת לצורך תיעוד, תעדוף ודיווח. אין חישוב מחירים/הקצאות מתוך הישויות הללו.

---

## הרשאות

- **תכנון מפורט:** תפקיד Development Editor.
- **ועדה:** תפקיד Committee Admin לסטטוס והחלטות.
- **ביצוע/התקדמות:** תפקיד Execution Manager לעדכונים בפועל.
- **הקצאה:** תפקיד Finance/Dev Cost Allocator לקיבוע והפקת דוחות.

---

## מילון שדות

### Plan – תוכנית בניין עיר

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| תב"ע ID | Plan ID | plan_id | uuid |
| שם תוכנית | Plan Name | plan_name | string |
| מספר תוכנית | Plan Number | plan_number | string |
| סטטוס תכנון | Planning Status | planning_status | enum(Draft,Submitted,Approved,Rejected) |
| תאריך אישור | Approval Date | approval_date | date |
| ייעודי קרקע | Land Use Map | land_use_map | json/file |
| גבולות | Boundaries | boundaries | geojson |
| הערות | Notes | notes | text |

### Lot – מגרש

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| מגרש ID | Lot ID | lot_id | uuid |
| תב"ע | Plan | plan_id | reference(Plan) |
| מספר מגרש | Lot Number | lot_number | string |
| גודל מגרש מ"ר | Lot Area sqm | area_sqm | decimal |
| לחיוב | Chargeable | chargeable | boolean |
| ייעוד | Zoning | zoning | enum(Residential,Commercial,Public,Other) |
| סטטוס פיתוח | Development Status | lot_development_status | enum(NotStarted,InProgress,Completed) |
| מחיר מ"ר פיתוח | Dev Price per sqm | dev_price_per_sqm | money(computed/locked) |
| עלות פיתוח מוקצית | Allocated Dev Cost | allocated_dev_cost | money(computed) |
| פרויקט קשור | Related Development Project | related_project | reference(DevelopmentProject,readonly) |
| בעלים | Owner | owner_name | string |
| הערות | Notes | notes | text |

### DevelopmentProjectLot – מגרשי פרויקט פיתוח

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| מגרש | Lot | lot | reference(Lot,reqd) |
| תב\"ע | Plan | plan | reference(Plan,readonly,fetched) |
| מספר מגרש | Lot Number | lot_number | string(readonly) |
| לחיוב | Chargeable | chargeable | boolean(readonly) |
| שטח לחישוב | Area (sqm) | area_sqm | decimal(readonly) |
| יחידות דיור | Housing Units | housing_units | int(readonly) |
| סטטוס פיתוח | Development Status | development_status | string(readonly) |
| הערות | Notes | notes | text |

### DevelopmentProject – פרויקט פיתוח

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| פרויקט פיתוח ID | Development Project ID | development_project_id | uuid |
| תב"ע | Plan | plan_id | reference(Plan) |
| שם פרויקט | Project Name | project_name | string |
| סטטוס פרויקט | Project Status | project_status | enum(Draft,UnderCommitteeReview,Approved,RevisionsRequired,Rejected,InExecution,Completed) |
| עלות מתוכננת | Planned Total Cost | planned_total_cost | money(computed) |
| עלות בפועל | Actual Total Cost | actual_total_cost | money(computed) |
| עלות להקצאה | Allocatable Total Cost | allocatable_total_cost | money |
| מחיר פיתוח למ"ר | Dev Price per sqm | dev_price_per_sqm | money(computed/locked) |
| תאריך התחלה משוער | Estimated Start Date | estimated_start_date | date |
| תאריך סיום משוער | Estimated End Date | estimated_end_date | date |
| מקור חישוב | Calculation Source | calculation_source | enum(Planned,Approved,Actual,ManualAdjustment) |
| נעילת מחיר | Price Locked | price_locked | boolean |
| תאריך נעילה | Price Lock Date | price_lock_date | date(readonly) |
| סיבת נעילה | Price Lock Reason | price_lock_reason | text |
| היסטוריית מחיר | Price History | price_history | table(Development Price History) |

### RegionalInfrastructureProject – פרויקט תשתיות על

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| שם פרויקט | Infrastructure Project Name | infrastructure_project_name | string |
| היקף | Project Scope | project_scope | text |
| מקור מימון | Funding Source | funding_source | string |
| סטטוס | Status | status | enum(Planning,UnderExecution,Completed,OnHold) |
| תאריך התחלה | Start Date | start_date | date |
| תאריך סיום | End Date | end_date | date |
| עלות משוערת כוללת | Total Estimate Cost | total_estimate_cost | money |
| עלות בפועל כוללת | Total Actual Cost | total_actual_cost | money |
| פרויקטי פיתוח מקושרים | Linked Development Projects | linked_projects | table(Regional Infrastructure Project Link) |
| מיקום | Location | location | geolocation |
| הערות | Notes | notes | text |

### RegionalInfrastructureProjectLink – קישורי פרויקטי פיתוח

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| פרויקט פיתוח | Development Project | development_project | reference(DevelopmentProject,reqd) |
| סטטוס פרויקט | Project Status | project_status | string(readonly,fetched) |
| הערות | Notes | notes | text |

### DevelopmentStage – שלב פיתוח

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| שלב ID | Stage ID | stage_id | uuid |
| פרויקט | Development Project | development_project_id | reference(DevelopmentProject) |
| שם שלב | Stage Name | stage_name | enum(StageA,StageB,Final) |
| סטטוס שלב | Stage Status | stage_status | enum(NotStarted,InProgress,Completed,OnHold) |
| אחוז התקדמות | Progress Percent | progress_percent | number(0-100,computed) |
| עלות מתוכננת | Planned Cost | planned_cost | money(computed) |
| עלות בפועל | Actual Cost | actual_cost | money(computed) |
| תאריך התחלה | Start Date | start_date | date |
| תאריך סיום | End Date | end_date | date |

### DevelopmentItem – סעיף פיתוח

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| סעיף ID | Item ID | item_id | uuid |
| שלב | Stage | stage_id | reference(DevelopmentStage) |
| קטגוריה | Category | category | enum(Earthworks,Sewer,Water,Electricity,Roads,Sidewalks,Lighting,Landscaping,PublicRealm,Other) |
| תיאור | Description | description | text |
| כמות | Quantity | quantity | decimal |
| יחידה | Unit | unit | enum(m, m2, m3, unit, lot, hour, day) |
| עלות יחידה | Unit Cost | unit_cost | money |
| עלות מתוכננת | Planned Cost | planned_cost | money(computed=quantity×unit_cost) |
| עלות בפועל | Actual Cost | actual_cost | money |
| סטטוס סעיף | Item Status | item_status | enum(Planned,InTender,InExecution,Completed,Canceled) |
| קבלן | Contractor | contractor_id | reference(Contractor) |
| הערות | Notes | notes | text |

### CommitteeReview – ועדה תוך־משרדית

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| דיון ID | Review ID | review_id | uuid |
| פרויקט | Development Project | development_project_id | reference(DevelopmentProject) |
| סטטוס ועדה | Committee Status | committee_status | enum(Pending,Approved,Rejected,RevisionsRequired) |
| סיכום | Summary | summary | text |
| תאריך דיון | Review Date | review_date | date |
| החלטות | Decisions | decisions | json/text |
| עלות מאושרת | Approved Allocatable Cost | approved_allocatable_cost | money |

### StageProgressUpdate – עדכון התקדמות שלב

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| עדכון ID | Update ID | progress_update_id | uuid |
| שלב | Stage | stage_id | reference(DevelopmentStage) |
| תאריך | Date | update_date | date |
| אחוז התקדמות | Progress Percent | progress_percent | number(0-100) |
| תיאור | Notes | notes | text |
| הוצאה בפועל | Actual Expense | actual_expense | money |

### CostAllocation – הקצאת עלויות

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| הקצאה ID | Allocation ID | allocation_id | uuid |
| פרויקט | Development Project | development_project_id | reference(DevelopmentProject) |
| מגרש | Lot | lot_id | reference(Lot) |
| שטח לחישוב | Chargeable Area sqm | chargeable_area_sqm | decimal |
| מחיר למ"ר | Price per sqm | price_per_sqm | money |
| עלות מוקצית | Allocated Cost | allocated_cost | money |
| מקור חישוב | Calculation Source | calculation_source | enum(Planned,Approved,Actual,ManualAdjustment) |
| תאריך חישוב | Calculation Date | calculation_date | date |
| נעול | Locked | locked | boolean |

### DevelopmentPriceHistory – היסטוריית מחיר למ"ר

| שם השדה בעברית | השם באנגלית | שם טכני | סוג |
|:---|:---|:---|:---|
| תאריך שינוי | Change Date | change_date | date |
| מחיר למ"ר | Price per sqm | price_per_sqm | money |
| מקור חישוב | Calculation Source | calculation_source | enum(Planned,Approved,Actual,ManualAdjustment) |
| נעול | Locked | locked | boolean |
| הערה | Note | note | text |

---

## הסברי שדות ולוגיקה (Per‑Field Behavior)

### Development Project

**Calculation Source:** מקור חישוב המשפיע על `allocatable_total_cost` שממנו נגזר `dev_price_per_sqm`.
- **Planned:** שימוש בסכום המתוכנן מכל ה־Items.
- **Approved:** שימוש בשדה `allocatable_total_cost` המאושר (לרוב לאחר ועדה).
- **Actual:** שימוש בסכום בפועל מכל ה־Items.
- **ManualAdjustment:** לא מחשב אוטומטית — ערך המחיר נשאר כפי שהוזן; דורש הרשאה.

**Allocatable Total Cost:** עלות כוללת שמוקצית בין המגרשים; משמשת עם Calculation Source=Approved. שינוי דורש הרצת הקצאה מחדש.

**Dev Price per sqm:** המחיר למ"ר המחושב: `allocatable_total_cost / Σ area_sqm (Chargeable=1)` מתוך רשימת `Development Project Lots`; נכתב לפרויקט ול־Lot בעת הקצאה.

**Price Locked:** סימון נעילה שמונע חישוב מחדש של `dev_price_per_sqm`. בעת נעילה נרשמת שורת היסטוריה.

**Price Lock Date:** תאריך הנעילה; נכתב אוטומטית בעת הפעלת נעילה.

**Price Lock Reason:** סיבת הנעילה (טקסט חופשי) — נועדה לתיעוד ואודיט. נשמרת בפרויקט ונכנסת גם ל־Price History (בשדה Note) בזמן הנעילה; מאפשר לזהות למה בוצעה נעילה (למשל: לאחר אישור ועדה/חתימת קבלן). אין מנגנון ניקוי אוטומטי בעת ביטול נעילה.

---

## לוגיקת אינטגרציה והקפדות

- **חיבור Plan↔Lot:** יצירת Lot מחייבת Plan קיים; שינוי Plan אסור אם קיימות הקצאות נעולות (`locked=true`).
- **חיבור Project↔Committee:** פרויקט לא יתקדם ל־InExecution ללא החלטת ועדה מאשרת.
- **חיבור Project↔CostAllocation:** הרצת הקצאה מאפשרת קיבוע מחיר למ"ר; שינוי לאחר קיבוע דורש ביטול נעילה בהרשאה מתאימה.
- **הצגת מחירים בטפסי Lot:** נסמכת על ההקצאה האחרונה הנעולה או האחרונה המחושבת (אם לא נעולה).

---

## דוגמה מסכמת לשלבי עבודה

- **שלב א:** עבודות עפר, הנחת ביוב/מים/חשמל ראשיים, כבישי גישה.
- **שלב ב:** חיבורי תשתיות למגרשים (מים, ביוב, חשמל וכו').
- **שלב גמר:** מדרכות, תאורה, גינון ונוף מתחמים ציבוריים.

---

## דוחות מוצעים

- **דוח הקצאה למגרשים** (לפי מגרש; פירוט שלבים/סעיפים; מחיר למ"ר; עלות מוקצית).
- **דוח סטטוס פרויקט** (לפי שלבים; תכנון מול ביצוע; חריגות עלות).
- **דוח ועדה** (החלטות, עלות מאושרת, שינויים נדרשים).
