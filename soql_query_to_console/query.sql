SELECT Id, WhatId, Subject, CreatedBy.Name, Description, CreatedDate
FROM Task
WHERE TaskSubtype = 'Call' AND CreatedDate = TODAY
