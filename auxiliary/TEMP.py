from report_app.report_logic.config import get_db_user, get_db_pass
from report_app.report_logic.database_manipulator import *

from sqlalchemy import text

sql_query = text("""
SELECT
	CASE WHEN srp2.sValue IS NULL THEN 'NULL' ELSE srp2.sValue END AS 'Источник поступления',
	CONVERT(NVARCHAR, cr.CreationDateTime, 20) AS 'Дата время создания заявки',
	sr.idSimpleRequest AS '№ Заявки',
	srp.sValue AS 'Причина закрытия счета',
	sr.sPinEq AS 'ПИН Клиента по заявке',
	d.Name AS 'Статус по заявке',
	CONVERT(NVARCHAR, l.ActionDateTime, 20) AS 'Дата время изменения статуса',
	CASE WHEN u.NAME LIKE '%Технич%' THEN 'Sistem' WHEN u.NAME='Technical_KK_sys' THEN 'Sistem' ELSE u.NAME END AS 'Пользователь изменивший статус ФИО пользователя',
	CASE WHEN u.NAME LIKE '%Технич%' THEN 'Sistem' WHEN u.NAME='Technical_KK_sys' THEN 'Sistem' ELSE u.WindowsLogin END AS 'Пользователь изменивший статус ФИО пользователя',
	CASE WHEN l.FinalStatusID IN (6659, 6657) THEN '+' ELSE '' END AS 'Маркер финального статуса по заявке',
	CASE WHEN l.FinalStatusID IN (6661, 6663) THEN '++' ELSE '' END AS 'Маркер статуса на удержании по заявке'
FROM LM1..vftSimpleRequest_listALL sr (NOLOCK)
	LEFT JOIN lm1..ftSimpleRequestProperty srp (NOLOCK) ON srp.idObject=sr.idSimpleRequest AND srp.idFieldType=480564
	LEFT JOIN lm1..ftSimpleRequestProperty srp2 (NOLOCK) ON srp2.idObject=sr.idSimpleRequest AND srp2.idFieldType=487569
	JOIN CB_CREDITCONVEYOR..CREDITREQUESTS cr ON cr.LMDealState=sr.idSimpleRequest
	JOIN CB_CREDITCONVEYOR.dbo.LOG L WITH (NOLOCK) ON L.RequestID = cr.RequestId
	JOIN CB_CREDITCONVEYOR.dbo.ACTIONS A WITH (NOLOCK) ON A.ID= L.ActionID
	JOIN CB_CREDITCONVEYOR.dbo.ROLES R WITH (NOLOCK) ON R.RoleID = L.RoleID
	JOIN CB_CREDITCONVEYOR.dbo.STATUSES D WITH (NOLOCK) ON L.FinalStatusID = D.ID
	JOIN CB_CREDITCONVEYOR.dbo.Users U WITH (NOLOCK) ON U.ID=l.UserID
WHERE 1=1
	AND sr.idSimpleRequestDocType=480562
	AND cr.CreationDateTime BETWEEN '01-01-2023' AND CAST(GETDATE() As Date)
ORDER BY sr.idSimpleRequest
""")

df = get_chunks(prepare_connection_url(host="rcdb-listener"), sql_query)
print(df.size)