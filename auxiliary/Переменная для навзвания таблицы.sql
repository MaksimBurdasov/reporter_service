DECLARE @log_table SYSNAME;
DECLARE @query NVARCHAR(MAX);

set @log_table = 'RCSITE.dbo.MaxLogs'

set @query = 'SELECT * FROM ' + @log_table;

EXEC sp_executesql @query