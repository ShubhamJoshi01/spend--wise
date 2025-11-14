-- Stored Procedures for Budget Management and Alerts
-- Run this file to set up stored procedures

USE expense_tracker;

DELIMITER $$

-- Procedure: Check budget status for a user and category
CREATE PROCEDURE check_budget_status(
    IN p_userid INT,
    IN p_categoryid INT,
    IN p_month INT
)
BEGIN
    DECLARE total_spent DECIMAL(10,2);
    DECLARE budget_limit DECIMAL(10,2);
    DECLARE budget_status VARCHAR(50);
    DECLARE remaining_budget DECIMAL(10,2);
    DECLARE percentage_used DECIMAL(5,2);
    
    -- Get budget limit
    SELECT limitamount, status INTO budget_limit, budget_status
    FROM budget
    WHERE userid = p_userid
      AND categoryid = p_categoryid
      AND month = p_month
      AND status = 'active'
    LIMIT 1;
    
    -- Calculate total spent
    SELECT COALESCE(SUM(amount), 0) INTO total_spent
    FROM transaction
    WHERE userid = p_userid
      AND categoryid = p_categoryid
      AND type = 'expense'
      AND MONTH(date) = p_month
      AND YEAR(date) = YEAR(CURDATE());
    
    -- Calculate remaining budget and percentage
    IF budget_limit IS NOT NULL THEN
        SET remaining_budget = budget_limit - total_spent;
        SET percentage_used = (total_spent / budget_limit) * 100;
        
        SELECT 
            p_userid AS userid,
            p_categoryid AS categoryid,
            p_month AS month,
            budget_limit AS limit_amount,
            total_spent AS spent_amount,
            remaining_budget AS remaining_amount,
            percentage_used AS percentage_used,
            budget_status AS status,
            CASE 
                WHEN total_spent >= budget_limit THEN 'EXCEEDED'
                WHEN total_spent >= (budget_limit * 0.9) THEN 'WARNING'
                ELSE 'OK'
            END AS alert_level;
    ELSE
        SELECT 
            p_userid AS userid,
            p_categoryid AS categoryid,
            p_month AS month,
            NULL AS limit_amount,
            total_spent AS spent_amount,
            NULL AS remaining_amount,
            NULL AS percentage_used,
            'NO_BUDGET' AS status,
            'N/A' AS alert_level;
    END IF;
END$$

-- Procedure: Get all active alerts for a user
CREATE PROCEDURE get_user_alerts(
    IN p_userid INT,
    IN p_unread_only BOOLEAN
)
BEGIN
    IF p_unread_only THEN
        SELECT 
            alertid,
            userid,
            budgetid,
            categoryid,
            (SELECT name FROM category WHERE categoryid = ba.categoryid) AS category_name,
            message,
            alert_type,
            created_at,
            is_read
        FROM budget_alerts ba
        WHERE userid = p_userid
          AND is_read = FALSE
        ORDER BY created_at DESC;
    ELSE
        SELECT 
            alertid,
            userid,
            budgetid,
            categoryid,
            (SELECT name FROM category WHERE categoryid = ba.categoryid) AS category_name,
            message,
            alert_type,
            created_at,
            is_read
        FROM budget_alerts ba
        WHERE userid = p_userid
        ORDER BY created_at DESC;
    END IF;
END$$

-- Procedure: Mark alert as read
CREATE PROCEDURE mark_alert_read(
    IN p_alertid INT
)
BEGIN
    UPDATE budget_alerts
    SET is_read = TRUE
    WHERE alertid = p_alertid;
END$$

-- Procedure: Check all budgets for a user and generate alerts
CREATE PROCEDURE check_all_budgets(
    IN p_userid INT,
    IN p_month INT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_budgetid INT;
    DECLARE v_categoryid INT;
    DECLARE v_limit DECIMAL(10,2);
    DECLARE v_total_spent DECIMAL(10,2);
    DECLARE v_alert_message TEXT;
    
    DECLARE budget_cursor CURSOR FOR
        SELECT budgetid, categoryid, limitamount
        FROM budget
        WHERE userid = p_userid
          AND month = p_month
          AND status = 'active';
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN budget_cursor;
    
    read_loop: LOOP
        FETCH budget_cursor INTO v_budgetid, v_categoryid, v_limit;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- Calculate total spent for this category
        SELECT COALESCE(SUM(amount), 0) INTO v_total_spent
        FROM transaction
        WHERE userid = p_userid
          AND categoryid = v_categoryid
          AND type = 'expense'
          AND MONTH(date) = p_month
          AND YEAR(date) = YEAR(CURDATE());
        
        -- Generate alert if needed
        IF v_total_spent >= v_limit THEN
            SET v_alert_message = CONCAT(
                'Budget EXCEEDED! Category: ',
                (SELECT name FROM category WHERE categoryid = v_categoryid),
                '. Limit: ', v_limit,
                ', Spent: ', v_total_spent
            );
            
            INSERT INTO budget_alerts (userid, budgetid, categoryid, message, alert_type)
            VALUES (p_userid, v_budgetid, v_categoryid, v_alert_message, 'exceeded')
            ON DUPLICATE KEY UPDATE 
                message = v_alert_message,
                is_read = FALSE,
                created_at = CURRENT_TIMESTAMP;
        END IF;
    END LOOP;
    
    CLOSE budget_cursor;
END$$

DELIMITER ;


