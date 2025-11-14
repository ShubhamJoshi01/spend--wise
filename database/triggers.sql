-- SQL Triggers for Budget Monitoring and Alerts
-- Run this file to set up triggers that monitor budget limits

USE expense_tracker;

-- Create alerts table to store budget warnings
CREATE TABLE IF NOT EXISTS budget_alerts (
    alertid INT NOT NULL AUTO_INCREMENT,
    userid INT NOT NULL,
    budgetid INT DEFAULT NULL,
    categoryid INT DEFAULT NULL,
    message TEXT NOT NULL,
    alert_type ENUM('warning', 'exceeded') NOT NULL DEFAULT 'warning',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (alertid),
    KEY idx_userid (userid),
    KEY idx_budgetid (budgetid),
    CONSTRAINT fk_alert_user FOREIGN KEY (userid) REFERENCES user(userid) ON DELETE CASCADE,
    CONSTRAINT fk_alert_budget FOREIGN KEY (budgetid) REFERENCES budget(budgetid) ON DELETE CASCADE,
    CONSTRAINT fk_alert_category FOREIGN KEY (categoryid) REFERENCES category(categoryid) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Trigger: Check budget limit after transaction INSERT
-- This trigger fires after an expense transaction is inserted
DELIMITER $$

CREATE TRIGGER check_budget_after_expense
AFTER INSERT ON transaction
FOR EACH ROW
BEGIN
    DECLARE total_spent DECIMAL(10,2);
    DECLARE budget_limit DECIMAL(10,2);
    DECLARE budget_status VARCHAR(50);
    DECLARE current_month INT;
    DECLARE alert_message TEXT;
    
    -- Only check for expense transactions
    IF NEW.type = 'expense' THEN
        SET current_month = MONTH(NEW.date);
        
        -- Check if there's an active budget for this user and category
        SELECT limitamount, status INTO budget_limit, budget_status
        FROM budget
        WHERE userid = NEW.userid
          AND categoryid = NEW.categoryid
          AND month = current_month
          AND status = 'active'
        LIMIT 1;
        
        -- If budget exists, calculate total spending
        IF budget_limit IS NOT NULL THEN
            SELECT COALESCE(SUM(amount), 0) INTO total_spent
            FROM transaction
            WHERE userid = NEW.userid
              AND categoryid = NEW.categoryid
              AND type = 'expense'
              AND MONTH(date) = current_month
              AND YEAR(date) = YEAR(NEW.date);
            
            -- Check if budget is exceeded (90% threshold for warning, 100% for exceeded)
            IF total_spent >= budget_limit THEN
                SET alert_message = CONCAT(
                    'Budget EXCEEDED! Category: ', 
                    (SELECT name FROM category WHERE categoryid = NEW.categoryid),
                    '. Limit: ', budget_limit, 
                    ', Spent: ', total_spent
                );
                
                INSERT INTO budget_alerts (userid, budgetid, categoryid, message, alert_type)
                VALUES (
                    NEW.userid,
                    (SELECT budgetid FROM budget 
                     WHERE userid = NEW.userid 
                       AND categoryid = NEW.categoryid 
                       AND month = current_month 
                       AND status = 'active' 
                     LIMIT 1),
                    NEW.categoryid,
                    alert_message,
                    'exceeded'
                );
            ELSEIF total_spent >= (budget_limit * 0.9) THEN
                SET alert_message = CONCAT(
                    'Budget WARNING: 90% threshold reached. Category: ',
                    (SELECT name FROM category WHERE categoryid = NEW.categoryid),
                    '. Limit: ', budget_limit,
                    ', Spent: ', total_spent,
                    ' (', ROUND((total_spent / budget_limit) * 100, 2), '%)'
                );
                
                INSERT INTO budget_alerts (userid, budgetid, categoryid, message, alert_type)
                VALUES (
                    NEW.userid,
                    (SELECT budgetid FROM budget 
                     WHERE userid = NEW.userid 
                       AND categoryid = NEW.categoryid 
                       AND month = current_month 
                       AND status = 'active' 
                     LIMIT 1),
                    NEW.categoryid,
                    alert_message,
                    'warning'
                );
            END IF;
        END IF;
    END IF;
END$$

DELIMITER ;

-- Trigger: Check budget limit after transaction UPDATE
DELIMITER $$

CREATE TRIGGER check_budget_after_update
AFTER UPDATE ON transaction
FOR EACH ROW
BEGIN
    DECLARE total_spent DECIMAL(10,2);
    DECLARE budget_limit DECIMAL(10,2);
    DECLARE budget_status VARCHAR(50);
    DECLARE current_month INT;
    DECLARE alert_message TEXT;
    
    -- Only check for expense transactions
    IF NEW.type = 'expense' THEN
        SET current_month = MONTH(NEW.date);
        
        -- Check if there's an active budget
        SELECT limitamount, status INTO budget_limit, budget_status
        FROM budget
        WHERE userid = NEW.userid
          AND categoryid = NEW.categoryid
          AND month = current_month
          AND status = 'active'
        LIMIT 1;
        
        IF budget_limit IS NOT NULL THEN
            SELECT COALESCE(SUM(amount), 0) INTO total_spent
            FROM transaction
            WHERE userid = NEW.userid
              AND categoryid = NEW.categoryid
              AND type = 'expense'
              AND MONTH(date) = current_month
              AND YEAR(date) = YEAR(NEW.date);
            
            IF total_spent >= budget_limit THEN
                SET alert_message = CONCAT(
                    'Budget EXCEEDED! Category: ',
                    (SELECT name FROM category WHERE categoryid = NEW.categoryid),
                    '. Limit: ', budget_limit,
                    ', Spent: ', total_spent
                );
                
                INSERT INTO budget_alerts (userid, budgetid, categoryid, message, alert_type)
                VALUES (
                    NEW.userid,
                    (SELECT budgetid FROM budget 
                     WHERE userid = NEW.userid 
                       AND categoryid = NEW.categoryid 
                       AND month = current_month 
                       AND status = 'active' 
                     LIMIT 1),
                    NEW.categoryid,
                    alert_message,
                    'exceeded'
                )
                ON DUPLICATE KEY UPDATE message = alert_message, is_read = FALSE;
            END IF;
        END IF;
    END IF;
END$$

DELIMITER ;


