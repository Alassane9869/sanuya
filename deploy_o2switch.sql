-- ============================================================
-- SCRIPT D'INITIALISATION DE LA BASE DE DONNÉES SANUYA SUR O2SWITCH
-- Base : vuxe8870_sanuya
-- Utilisateur : vuxe8870_sanuya_bko
-- Domaine : sanuya.danayaplus.com
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Création de la table principale des signalements
CREATE TABLE IF NOT EXISTS `signalements` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `latitude` DOUBLE NOT NULL,
    `longitude` DOUBLE NOT NULL,
    `volume` DOUBLE DEFAULT 0.0,
    `priorite` VARCHAR(50) DEFAULT 'normal',
    `statut` VARCHAR(50) DEFAULT 'en_attente',
    `date_creation` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `photo_nom` VARCHAR(255) NULL,
    `photo_chemin` VARCHAR(500) NULL,
    `dechets_detectes` TEXT NULL,
    `nb_dechets` INT DEFAULT 1,
    `est_doublon` TINYINT(1) DEFAULT 0,
    `doublon_de` INT NULL,
    INDEX `idx_statut` (`statut`),
    INDEX `idx_priorite` (`priorite`),
    INDEX `idx_coords` (`latitude`, `longitude`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Insertion des données réelles initiales de Bamako
INSERT INTO `signalements` (`id`, `latitude`, `longitude`, `volume`, `priorite`, `statut`, `date_creation`, `photo_nom`, `photo_chemin`, `dechets_detectes`, `nb_dechets`, `est_doublon`, `doublon_de`) VALUES
(1, 12.6392, -8.0029, 2.5, 'urgent', 'en_attente', '2026-08-11 10:00:00', 'depot1.jpg', 'images_test/depot1.jpg', 'Plastiques, gravats, dechets menagers', 1, 0, NULL),
(2, 12.6500, -7.9800, 4.0, 'urgent', 'en_cours', '2026-08-11 11:30:00', 'depot2.jpg', 'images_test/depot2.jpg', 'Sacs plastiques, cartons volumineux', 2, 0, NULL),
(3, 12.6300, -8.0200, 1.2, 'normal', 'resolu', '2026-08-10 09:00:00', 'depot3.jpg', 'images_test/depot3.jpg', 'Bouteilles plastiques, dechets divers', 1, 0, NULL),
(4, 12.6450, -8.0100, 3.1, 'urgent', 'en_attente', '2026-08-11 14:15:00', 'depot4.jpg', 'images_test/depot4.jpg', 'Depot mixte, matieres plastiques', 1, 0, NULL),
(5, 12.6200, -7.9900, 0.8, 'moyen', 'resolu', '2026-08-09 16:45:00', 'depot5.jpg', 'images_test/depot5.jpg', 'Dechets organiques, plastiques legers', 1, 0, NULL)
ON DUPLICATE KEY UPDATE 
    `volume` = VALUES(`volume`), 
    `priorite` = VALUES(`priorite`), 
    `statut` = VALUES(`statut`);

SET FOREIGN_KEY_CHECKS = 1;
