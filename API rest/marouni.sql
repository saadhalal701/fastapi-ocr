-- MySQL dump 10.13
--
-- Host: localhost    Database: marouni
-- ------------------------------------------------------
-- Server version	(Version compatible)

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Création de la base de données avec un classement plus compatible
CREATE DATABASE IF NOT EXISTS `projet` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `projet`;

--
-- Table structure for table `utilisateur`
--
DROP TABLE IF EXISTS `utilisateur`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `utilisateur` (
  `iduser` INT NOT NULL AUTO_INCREMENT,
  `nomUser` VARCHAR(255) NOT NULL,
  `prenomUser` VARCHAR(45) DEFAULT NULL,
  `emailUser` VARCHAR(45) DEFAULT NULL UNIQUE,
  `telUser` VARCHAR(45) DEFAULT NULL,
  `passwordUser` VARCHAR(255) DEFAULT NULL, -- Longueur augmentée pour les mots de passe hachés
  PRIMARY KEY (`iduser`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- Utilisation du classement compatible
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `station`
--
DROP TABLE IF EXISTS `station`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `station` (
  `idstation` INT NOT NULL AUTO_INCREMENT,
  `nomStation` VARCHAR(45) NOT NULL,
  `localisation` VARCHAR(45) DEFAULT NULL,
  `tarifStation` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`idstation`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- Utilisation du classement compatible
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vehicule`
--
DROP TABLE IF EXISTS `vehicule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vehicule` (
  `idvehicule` INT NOT NULL AUTO_INCREMENT,
  `plaqueImmat` VARCHAR(45) NOT NULL UNIQUE, -- Rendu NOT NULL et UNIQUE
  `marque` VARCHAR(45) DEFAULT NULL,
  `modele` VARCHAR(45) DEFAULT NULL,
  `iduser` INT DEFAULT NULL,
  `photo` BLOB DEFAULT NULL, -- Champ photo ajouté selon le modèle Python
  PRIMARY KEY (`idvehicule`),
  KEY `fk_vehicule_utilisateur_idx` (`iduser`),
  CONSTRAINT `fk_vehicule_utilisateur` FOREIGN KEY (`iduser`) REFERENCES `utilisateur` (`iduser`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- Utilisation du classement compatible
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `passage`
--
DROP TABLE IF EXISTS `passage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `passage` (
  `idpassage` INT NOT NULL AUTO_INCREMENT,
  `datePassage` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Ajout de DEFAULT CURRENT_TIMESTAMP
  `montant` DECIMAL(10,2) DEFAULT NULL,
  `photoPassage` BLOB DEFAULT NULL,
  `idvehicule` INT NOT NULL, -- Rendu NOT NULL
  `idstation` INT NOT NULL, -- Rendu NOT NULL
  PRIMARY KEY (`idpassage`),
  KEY `fk_passage_vehicule_idx` (`idvehicule`),
  KEY `fk_passage_station_idx` (`idstation`),
  CONSTRAINT `fk_passage_vehicule` FOREIGN KEY (`idvehicule`) REFERENCES `vehicule` (`idvehicule`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_passage_station` FOREIGN KEY (`idstation`) REFERENCES `station` (`idstation`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- Utilisation du classement compatible
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `paiement`
--
DROP TABLE IF EXISTS `paiement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paiement` (
  `idpaiement` INT NOT NULL AUTO_INCREMENT,
  `montant` DECIMAL(10,2) NOT NULL,
  `date` DATETIME DEFAULT CURRENT_TIMESTAMP, -- Ajout de DEFAULT CURRENT_TIMESTAMP
  `idpassage` INT DEFAULT NULL,
  PRIMARY KEY (`idpaiement`),
  KEY `fk_paiement_passage_idx` (`idpassage`),
  CONSTRAINT `fk_paiement_passage` FOREIGN KEY (`idpassage`) REFERENCES `passage` (`idpassage`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- Utilisation du classement compatible
/*!40101 SET character_set_client = @saved_cs_client */;


/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on YYYY-MM-DD HH:MM:SS
