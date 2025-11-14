-- Schema export for database `expense_tracker`

CREATE TABLE `budget` (
  `budgetid` int NOT NULL AUTO_INCREMENT,
  `userid` int DEFAULT NULL,
  `categoryid` int DEFAULT NULL,
  `limitamount` decimal(10,2) DEFAULT NULL,
  `month` int DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`budgetid`),
  KEY `userid` (`userid`),
  KEY `categoryid` (`categoryid`),
  CONSTRAINT `budget_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `user` (`userid`),
  CONSTRAINT `budget_ibfk_2` FOREIGN KEY (`categoryid`) REFERENCES `category` (`categoryid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `category` (
  `categoryid` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  PRIMARY KEY (`categoryid`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `login` (
  `userid` int NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`userid`),
  CONSTRAINT `login_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `user` (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `paymentmethod` (
  `methodid` int NOT NULL AUTO_INCREMENT,
  `type` varchar(50) NOT NULL,
  `details` text,
  PRIMARY KEY (`methodid`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `transaction` (
  `transid` int NOT NULL AUTO_INCREMENT,
  `userid` int DEFAULT NULL,
  `categoryid` int DEFAULT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `type` enum('income','expense') NOT NULL,
  `date` date DEFAULT NULL,
  `paymentmethod` int DEFAULT NULL,
  PRIMARY KEY (`transid`),
  KEY `userid` (`userid`),
  KEY `categoryid` (`categoryid`),
  KEY `paymentmethod` (`paymentmethod`),
  CONSTRAINT `transaction_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `user` (`userid`),
  CONSTRAINT `transaction_ibfk_2` FOREIGN KEY (`categoryid`) REFERENCES `category` (`categoryid`),
  CONSTRAINT `transaction_ibfk_3` FOREIGN KEY (`paymentmethod`) REFERENCES `paymentmethod` (`methodid`)
) ENGINE=InnoDB AUTO_INCREMENT=108 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user` (
  `userid` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `contact` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`userid`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

