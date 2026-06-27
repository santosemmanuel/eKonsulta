-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 19, 2026 at 07:34 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.1.25

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
(8, 'DEVARAS', 'QUINIE', 'PAMAT', 'DUMALAG (PUSOD)', '132505899508', 'Member', 'P012606170051901', '2026-06-17 11:01:54');

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
(4, 'SANTOS', 'EMMANUEL', 'BARBOSA', 'POBLACION DISTRICT I', '12345678900', 'Member', 'P0606162026123', '2026-06-19 01:29:34');

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
(17, 'JOPET', 'DEL AGUA', 'JOPET', 'jopet@MHO123', 'user');

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `cec_transfer`
--
ALTER TABLE `cec_transfer`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
