# this will give an error message in the b3.log, 
# but the IF I came up with to test if the field exists is giving me an error too
ALTER TABLE `%s` ADD `id_token` VARCHAR(10) NOT NULL DEFAULT '';

ALTER TABLE `%s` CHANGE `id` `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT;
