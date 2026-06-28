-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 28, 2026 at 04:17 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `mhob_ekonsulta_forms`
--
CREATE DATABASE IF NOT EXISTS `mhob_ekonsulta_forms` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `mhob_ekonsulta_forms`;

-- --------------------------------------------------------

--
-- Table structure for table `cec_registration`
--

CREATE TABLE `cec_registration` (
  `id` int(11) NOT NULL,
  `LastName` varchar(100) NOT NULL,
  `FirstName` varchar(100) NOT NULL,
  `MiddleName` varchar(100) DEFAULT NULL,
  `Barangay` varchar(150) DEFAULT NULL,
  `PIN` varchar(50) NOT NULL,
  `MemDep` enum('Member','Dependent','N/A') DEFAULT 'N/A',
  `PCUTransaction` varchar(100) DEFAULT 'N/A',
  `DateTimeProccess` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `cec_registration`
--

INSERT INTO `cec_registration` (`id`, `LastName`, `FirstName`, `MiddleName`, `Barangay`, `PIN`, `MemDep`, `PCUTransaction`, `DateTimeProccess`) VALUES
(7, 'PARADO', 'ELISA', 'MELIBO', 'DUMALAG (PUSOD)', '132503935582', 'Dependent', 'P012606170032771', '2026-06-17 09:55:33'),
(8, 'DEVARAS', 'QUINIE', 'PAMAT', 'DUMALAG (PUSOD)', '132505899508', 'Member', 'P012606170051901', '2026-06-17 11:01:54'),
(14, 'REFORZADO', 'MELBETH', 'DAZO', 'TAKIN', '132012421420', 'Member', 'N/A', '2026-06-23 11:31:46'),
(15, 'LASCOSTA', 'NATASHA', 'REFORZADO', 'TAKIN', '042516134504', 'Dependent', 'N/A', '2026-06-23 11:40:53'),
(16, 'RELLESIVA', 'LIZA', 'LANZAROTE', 'TAKIN', '132503885984', 'Member', 'P012606230060703', '2026-06-23 11:40:57'),
(17, 'ABRILLO', 'MICHELLE', 'CABELOS', 'TAKIN', '132027927460', 'Member', 'P012606230061627', '2026-06-23 11:45:20'),
(18, 'CELEDIO', 'MARRY ANN', 'MAGNO', 'TAKIN', '132027569777', 'Member', 'P012606230063295', '2026-06-23 11:53:35'),
(23, 'DEL PILAR', 'JOSELITO', 'PERANTE', 'GITABLAN', '130000830918', 'Member', 'P012606250022255', '2026-06-25 09:18:51'),
(24, 'ESCOBAL', 'REMEDIOS', 'LASTIMADO', 'GITABLAN', '131751710442', 'Member', 'P012606250024298', '2026-06-25 09:24:46'),
(25, 'MERIDOR', 'ANGELITA', 'CONDES', 'GITABLAN', '011753171691', 'Member', 'P012606250022255', '2026-06-25 09:26:40'),
(26, 'MERIDOR', 'ADRIANO', 'BERNAL', 'GITABLAN', '010502893837', 'Member', 'P012606250026821', '2026-06-25 09:33:22'),
(27, 'PALAÑA', 'ALMA', 'MENDOL', 'GITABLAN', '130250137924', 'Member', 'P012606250027348', '2026-06-25 09:34:43'),
(28, 'DAGAMI', 'LORAINE', 'ORONOS', 'GITABLAN', '130252724800', 'Member', 'P012606250032790', '2026-06-25 09:51:21'),
(29, 'AGRAVA', 'CECILIA', 'UDTOHAN', 'HUGPA EAST', '132503979296', 'Member', 'P012606250033270', '2026-06-25 09:52:57'),
(30, 'RIVAS', 'YOLANDA', 'FUNCION', 'GITABLAN', '13-025067239-0', 'Member', 'P012606250035053', '2026-06-25 09:59:05'),
(31, 'EQUIPAJE', 'AMBROCIO', 'MONTE', 'HUGPA EAST', '132021209329', 'Member', 'P012606250035419', '2026-06-25 09:59:34'),
(32, 'CABO', 'MA. NENET', 'GERALDE', 'HUGPA EAST', '132012469385', 'Member', 'P012606250037100', '2026-06-25 10:05:16'),
(33, 'RIVAS', 'REA', 'FUNCION', 'GITABLAN', '132529900167', 'Dependent', 'P012606250038655', '2026-06-25 10:12:33'),
(34, 'NELSON', 'MONTE', 'CABO', 'HUGPA EAST', '19-090050828-3', 'Member', 'P012604220006091', '2026-06-25 10:14:43'),
(35, 'BINATAC', 'SANTIAGO', 'BELARMINO', 'HUGPA EAST', '130001180445', 'Member', 'P012604070011829', '2026-06-25 10:24:17'),
(36, 'CONDES', 'EME', 'AGRAVA', 'HUGPA EAST', '13-202055749-8', 'Member', 'P012606250045020', '2026-06-25 10:35:44'),
(37, 'SINGKOY', 'RANDY', 'GENETA', 'GITABLAN', '082013959621', 'Member', 'P012606250048319', '2026-06-25 10:50:17'),
(38, 'CADION', 'JONATHAN', 'AGRAVA', 'HUGPA EAST', '132012474052', 'Member', 'P012606250053081', '2026-06-25 11:05:59'),
(39, 'DAGAMI', 'WENDILYN', 'CARDINAL', 'HUGPA EAST', '132027311583', 'Member', 'P012606250054080', '2026-06-25 11:08:56'),
(40, 'ESCOBAL', 'MIRASOL', 'BUENO', 'GITABLAN', '13-202943744-4', 'Member', 'P012606250053892', '2026-06-25 11:10:23'),
(41, 'ESPLANADA', 'HERBERT', 'GARCIA', 'POBLACION DISTRICT I', '130500510308', 'Member', 'P012604300020066', '2026-06-25 11:13:22');

-- --------------------------------------------------------

--
-- Table structure for table `cec_transfer`
--

CREATE TABLE `cec_transfer` (
  `id` int(11) NOT NULL,
  `LastName` varchar(100) NOT NULL,
  `FirstName` varchar(100) NOT NULL,
  `MiddleName` varchar(100) DEFAULT NULL,
  `Barangay` varchar(150) DEFAULT NULL,
  `PIN` varchar(50) NOT NULL,
  `MemDep` enum('Member','Dependent','N/A') DEFAULT 'N/A',
  `PCUTransaction` varchar(100) DEFAULT 'N/A',
  `DateTimeProccess` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `cec_transfer`
--

INSERT INTO `cec_transfer` (`id`, `LastName`, `FirstName`, `MiddleName`, `Barangay`, `PIN`, `MemDep`, `PCUTransaction`, `DateTimeProccess`) VALUES
(5, 'RAGA', 'GEMARIE', 'REFORZADO', 'TAKIN', '132012558930', 'Member', 'P012606230059010', '2026-06-23 11:30:51'),
(6, 'ORONOS', 'LUZVIMINDA', 'PALOMO', 'HUGPA EAST', '130000806561', 'Member', 'P012606250037365', '2026-06-25 10:07:13'),
(8, 'DEGENIO', 'MARIETA', 'REFUERZO', 'HUGPA EAST', '132503812650', 'Dependent', 'P012606250045100', '2026-06-25 10:37:50'),
(9, 'RIVAS', 'WEVINA', 'GO', 'GITABLAN', '131751746404', 'Member', 'N/A', '2026-06-25 11:16:51');

-- --------------------------------------------------------

--
-- Table structure for table `transmittal`
--

CREATE TABLE `transmittal` (
  `id` int(11) NOT NULL,
  `pin` varchar(12) NOT NULL,
  `lastName` varchar(225) NOT NULL,
  `firstName` varchar(225) NOT NULL,
  `middleName` varchar(225) NOT NULL,
  `ext` varchar(225) NOT NULL,
  `birthday` varchar(225) NOT NULL,
  `memberDepent` enum('Member','Dependent','','') NOT NULL,
  `generatedDate` date NOT NULL,
  `dateScanned` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `firstName` varchar(255) NOT NULL,
  `lastName` varchar(255) DEFAULT NULL,
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `position` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `firstName`, `lastName`, `username`, `password`, `position`) VALUES
(1, 'Admin', 'Admin', 'Admin1', 'admin@MHO123', 'admin'),
(2, 'MARLON', 'DE LA CRUZ', 'MARLON', 'marlon@MHO123', 'user'),
(3, 'CHRISTINE', 'MONTABON', 'TIN', 'tin@MHO123', 'user'),
(4, 'JONARD', 'POLANCOS', 'JONARD', 'jonard@MHO123', 'user'),
(5, 'IVY', 'ABLAY', 'IVY', 'ivy@MHO123', 'user'),
(6, 'KEVIN', 'MAGSAMBOL', 'KEVIN', 'kevin@MHO123', 'user'),
(7, 'ZOE', 'REMONTE', 'ZOE', 'zoe@MHO123', 'user'),
(8, 'MACE', 'ALFONSO', 'MACE', 'mace@MHO123', 'user'),
(9, 'EMMAN', 'SANTOS', 'EMMAN', '1', 'user'),
(10, 'JADE', 'RENOMERON', 'JADE', 'jade@MHO123', 'user'),
(11, 'QUENNIE', 'CONDE', 'QUENNIE', 'quennie@MHO123', 'user'),
(12, 'REGINE', 'LAUDE', 'REGINE', 'regine@MHO123', 'user'),
(16, 'DENNIS', 'MAPUSAO', 'DENNIS', 'dennis@MHO123', 'user'),
(17, 'JOPET', 'DEL AGUA', 'JOPET', 'jopet@MHO123', 'user'),
(18, 'Jeffrey', 'Sencio', 'JEFF', 'jeff@MHO123', 'scanner');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `cec_registration`
--
ALTER TABLE `cec_registration`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_pin` (`PIN`);

--
-- Indexes for table `cec_transfer`
--
ALTER TABLE `cec_transfer`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_pin` (`PIN`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `cec_registration`
--
ALTER TABLE `cec_registration`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=42;

--
-- AUTO_INCREMENT for table `cec_transfer`
--
ALTER TABLE `cec_transfer`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
