-- phpMyAdmin SQL Dump
-- version 3.4.5
-- http://www.phpmyadmin.net
--
-- Client: localhost
-- Généré le : Ven 18 Novembre 2016 à 20:10
-- Version du serveur: 5.6.14
-- Version de PHP: 5.2.13

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Base de données: 'eg_test_no_sqla'
--

-- --------------------------------------------------------

--
-- Structure de la table 'choices'
--

DROP TABLE IF EXISTS choices;
CREATE TABLE IF NOT EXISTS choices (
  id int(11) NOT NULL AUTO_INCREMENT,
  `status` int(11) DEFAULT NULL,
  datastring text,
  roundid int(11) DEFAULT NULL,
  assignmentId varchar(128) NOT NULL,
  workerId varchar(128) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY id (id),
  KEY fk_choice_part_id (assignmentId,workerId),
  KEY fk_choice_round_id (roundid)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1387 ;

-- --------------------------------------------------------

--
-- Structure de la table 'decisions'
--

DROP TABLE IF EXISTS decisions;
CREATE TABLE IF NOT EXISTS decisions (
  id int(11) NOT NULL AUTO_INCREMENT,
  `status` int(11) DEFAULT NULL,
  num int(11) DEFAULT NULL,
  `value` double DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  datastring text,
  reward double DEFAULT NULL,
  choiceid int(11) DEFAULT NULL,
  imageid int(11) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY fk_decision_choice_id (choiceid)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=845 ;

-- --------------------------------------------------------

--
-- Structure de la table 'games'
--

DROP TABLE IF EXISTS games;
CREATE TABLE IF NOT EXISTS games (
  id int(11) NOT NULL AUTO_INCREMENT,
  num int(11) DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  numExpectedParticipants int(11) DEFAULT NULL,
  numRounds int(11) DEFAULT NULL,
  datastring text,
  gamesetid int(11) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY fk_game_gameset_id (gamesetid)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=79 ;

-- --------------------------------------------------------

--
-- Structure de la table 'gamesets'
--

DROP TABLE IF EXISTS gamesets;
CREATE TABLE IF NOT EXISTS gamesets (
  id int(11) NOT NULL AUTO_INCREMENT,
  `status` int(11) DEFAULT NULL,
  numExpectedParticipants int(11) DEFAULT NULL,
  numGames int(11) DEFAULT NULL,
  pic_name text,
  starttime datetime DEFAULT NULL,
  playmode text,
  job_id varchar(128) DEFAULT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=61 ;

-- --------------------------------------------------------

--
-- Structure de la table 'image'
--

DROP TABLE IF EXISTS image;
CREATE TABLE IF NOT EXISTS image (
  id int(11) NOT NULL AUTO_INCREMENT,
  pic_name varchar(128) DEFAULT NULL,
  percent int(11) DEFAULT NULL,
  complexity int(11) DEFAULT NULL,
  color varchar(128) DEFAULT NULL,
  pic_type varchar(128) NOT NULL,
  `status` int(11) DEFAULT NULL,
  gameid int(11) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY fk_image_game_id (gameid)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=96 ;

-- --------------------------------------------------------

--
-- Structure de la table 'keycode_gameset_user'
--

DROP TABLE IF EXISTS keycode_gameset_user;
CREATE TABLE IF NOT EXISTS keycode_gameset_user (
  keyCodeBegin varchar(128) NOT NULL,
  creationtime datetime DEFAULT NULL,
  usagetime datetime DEFAULT NULL,
  userid int(11) NOT NULL,
  gamesetid int(11) NOT NULL,
  keyCodeEnd varchar(128) NOT NULL,
  totalreward double DEFAULT NULL,
  `status` varchar(128) NOT NULL,
  cwf_contributor_id varchar(128) DEFAULT NULL,
  bonus varchar(10) DEFAULT NULL,
  paidtime datetime DEFAULT NULL,
  resultpaycode varchar(128) DEFAULT NULL,
  resultpaymessage text,
  PRIMARY KEY (keyCodeBegin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table 'participants'
--

DROP TABLE IF EXISTS participants;
CREATE TABLE IF NOT EXISTS participants (
  assignmentId varchar(128) NOT NULL,
  workerId varchar(128) NOT NULL,
  hitId varchar(128) DEFAULT NULL,
  ipaddress varchar(128) DEFAULT NULL,
  cond int(11) DEFAULT NULL,
  counterbalance int(11) DEFAULT NULL,
  codeversion varchar(128) DEFAULT NULL,
  beginhit datetime DEFAULT NULL,
  beginexp datetime DEFAULT NULL,
  endhit datetime DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  debriefed tinyint(1) DEFAULT NULL,
  datastring text,
  userid int(11) DEFAULT NULL,
  PRIMARY KEY (assignmentId,workerId),
  KEY fk_participant_user_id (userid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Structure de la table 'participant_status'
--

DROP TABLE IF EXISTS participant_status;
CREATE TABLE IF NOT EXISTS participant_status (
  participant_statuscode int(11) NOT NULL AUTO_INCREMENT,
  participant_statuslib varchar(128) NOT NULL,
  PRIMARY KEY (participant_statuscode)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=9 ;

-- --------------------------------------------------------

--
-- Structure de la table 'questionnaires'
--

DROP TABLE IF EXISTS questionnaires;
CREATE TABLE IF NOT EXISTS questionnaires (
  id int(11) NOT NULL AUTO_INCREMENT,
  `status` int(11) DEFAULT NULL,
  userid int(11) DEFAULT NULL,
  gamesetid int(11) DEFAULT NULL,
  enterQtime datetime DEFAULT NULL,
  leaveQtime datetime DEFAULT NULL,
  extraverted int(11) DEFAULT NULL,
  critical int(11) DEFAULT NULL,
  dependable int(11) DEFAULT NULL,
  anxious int(11) DEFAULT NULL,
  `open` int(11) DEFAULT NULL,
  reserved int(11) DEFAULT NULL,
  sympathetic int(11) DEFAULT NULL,
  disorganized int(11) DEFAULT NULL,
  calm int(11) DEFAULT NULL,
  conventional int(11) DEFAULT NULL,
  sexe int(11) DEFAULT NULL,
  nativespeakenglish int(11) DEFAULT NULL,
  schoolgrade int(11) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY fk_questionnaire_user_id (userid)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=4 ;

-- --------------------------------------------------------

--
-- Structure de la table 'rounds'
--

DROP TABLE IF EXISTS rounds;
CREATE TABLE IF NOT EXISTS rounds (
  id int(11) NOT NULL AUTO_INCREMENT,
  num int(11) DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  `type` int(11) DEFAULT NULL,
  datastring text,
  startTime datetime DEFAULT NULL,
  endTime datetime DEFAULT NULL,
  maxreward double DEFAULT NULL,
  gameid int(11) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY fk_round_game_id (gameid)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=102 ;

-- --------------------------------------------------------

--
-- Structure de la table 'users'
--

DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users (
  id int(11) NOT NULL AUTO_INCREMENT,
  username varchar(128) DEFAULT NULL,
  `password` varchar(128) DEFAULT NULL,
  lastvisit datetime DEFAULT NULL,
  sessionId varchar(128) DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  datastring text,
  email text,
  ipaddress varchar(128) DEFAULT NULL,
  ip_in_use varchar(1) DEFAULT NULL,
  note text,
  PRIMARY KEY (id)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=164 ;

--
-- Contraintes pour les tables exportées
--

--
-- Contraintes pour la table `choices`
--
ALTER TABLE `choices`
  ADD CONSTRAINT fk_choice_part_id FOREIGN KEY (assignmentId, workerId) REFERENCES participants (assignmentId, workerId) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT fk_choice_round_id FOREIGN KEY (roundid) REFERENCES rounds (id) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `decisions`
--
ALTER TABLE `decisions`
  ADD CONSTRAINT fk_decision_choice_id FOREIGN KEY (choiceid) REFERENCES choices (id) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `games`
--
ALTER TABLE `games`
  ADD CONSTRAINT fk_game_gameset_id FOREIGN KEY (gamesetid) REFERENCES gamesets (id) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `image`
--
ALTER TABLE `image`
  ADD CONSTRAINT fk_image_game_id FOREIGN KEY (gameid) REFERENCES games (id) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `participants`
--
ALTER TABLE `participants`
  ADD CONSTRAINT fk_participant_user_id FOREIGN KEY (userid) REFERENCES `users` (id) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `questionnaires`
--
ALTER TABLE `questionnaires`
  ADD CONSTRAINT fk_questionnaire_user_id FOREIGN KEY (userid) REFERENCES `users` (id) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `rounds`
--
ALTER TABLE `rounds`
  ADD CONSTRAINT fk_round_game_id FOREIGN KEY (gameid) REFERENCES games (id) ON DELETE CASCADE ON UPDATE CASCADE;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
