
# Dohler O2C Rules
ZRED_T_P2P_DET — rule detail raporu —> Rule ID’yi ZRED01 işlem kodundan bulmalısın.

* ==**DOH-001**==
  * RULE: O2C_DOH_001_D011
  * DOCUMENT TYPE = COMMISSION THEN LOW RISK (ZCOM) ✅
  * ANOTHER TYPE  THEN HIGH RISK ✅
  * FIORI REPORT —> COMPANY CODE, USER AND AMOUNT IN RF CURRENCY ✅
  * YEAR OF CREATION OF THE DOCUMENT ✅
* ==**DOH-002** ✅==
  * RULE: O2C_DOH_002_D011
  * DOCUMENT TYPE = ZMUN THEN LOW RISK
  * ANOTHER TYPE  THEN HIGH RISK
* ==**DOH-003** ✅==
  * KEEP IT
* ==**DOH-004** ✅==
  * KEEP IT
* ==**DOH-005** (O2C_DOH_005_01_D060) ✅==
  * IF IT’S THE SAME DAY — NOTHING
  * OTHERWISE - HIGH RISK
        <!-- This image is a part of a business process or analysis interface with the title "Operation Type - Time elapsed between events". It is used to calculate the time between events and detect anomalies. The main text highlights the importance of evaluating the time elapsed, suggesting scenarios like "Payments made before goods receipt." 

  The interface includes a dropdown labeled "Select Event" with options such as "BL | Create Invoice I..." and "OD | Post Goods ...", indicating a focus on logistics and financial processes. The operation setup checks if the time between events like "Create Invoice" and "Post Goods" is greater than 24 hours, chosen as a unit of measure. "Remove" link in red suggests a feature to delete this setup.

  The design promotes operational efficiency and anomaly detection in events dependent on time, possibly in sectors like logistics or financial monitoring. The example scenario highlights the criticality of checking anomalies like payments made before receiving goods.
  ![](assets/image.png)
  Billing > GI + 24H
* **DOH-006** O2C_DOH_006_01_D011
  * IF IT’S CRONACLE — LOW RISK - OTHERWISE - HIGH RISK —> There will be two risks LOW & HIGH ✅
  * ADD ORDER VALUE ✅
  * ADD CUSTOMER ✅
* ==**DOH-007** ✅==
  * KEEP IT