CREATE TABLE IF NOT EXISTS `%s` (
  `id` MEDIUMINT(8) UNSIGNED NOT NULL AUTO_INCREMENT,
  `target_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `killer_id` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `kills` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  `retals` SMALLINT(5) UNSIGNED NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `target_id` (`target_id`),
  KEY `killer_id` (`killer_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;