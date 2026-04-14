-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: vellum_db
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `auditoria_ventas`
--

LOCK TABLES `auditoria_ventas` WRITE;
/*!40000 ALTER TABLE `auditoria_ventas` DISABLE KEYS */;
/*!40000 ALTER TABLE `auditoria_ventas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `carrito_temporal`
--

LOCK TABLES `carrito_temporal` WRITE;
/*!40000 ALTER TABLE `carrito_temporal` DISABLE KEYS */;
/*!40000 ALTER TABLE `carrito_temporal` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `detalle_ordenes_compra`
--

LOCK TABLES `detalle_ordenes_compra` WRITE;
/*!40000 ALTER TABLE `detalle_ordenes_compra` DISABLE KEYS */;
INSERT INTO `detalle_ordenes_compra` VALUES (1,1,2,20.00,5000.00,100000.00,1),(2,3,3,40.00,100.00,4000.00,2),(3,2,1,25.00,3000.00,75000.00,NULL),(4,4,1,15.00,800.00,12000.00,3),(5,5,4,100.00,1.00,100.00,4),(6,6,1,1000.00,8.00,8000.00,5);
/*!40000 ALTER TABLE `detalle_ordenes_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `detalle_ventas`
--

LOCK TABLES `detalle_ventas` WRITE;
/*!40000 ALTER TABLE `detalle_ventas` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalle_ventas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `estados_mexico`
--

LOCK TABLES `estados_mexico` WRITE;
/*!40000 ALTER TABLE `estados_mexico` DISABLE KEYS */;
INSERT INTO `estados_mexico` VALUES (1,'Aguascalientes',1,NULL),(2,'Baja California',1,NULL),(3,'Baja California Sur',1,NULL),(4,'Campeche',1,NULL),(5,'Chiapas',1,NULL),(6,'Chihuahua',1,NULL),(7,'Ciudad de México',1,NULL),(8,'Coahuila',1,NULL),(9,'Colima',1,NULL),(10,'Durango',1,NULL),(11,'Estado de México',1,NULL),(12,'Guanajuato',1,NULL),(13,'Guerrero',1,NULL),(14,'Hidalgo',1,NULL),(15,'Jalisco',1,NULL),(16,'Michoacán',1,NULL),(17,'Morelos',1,NULL),(18,'Nayarit',1,NULL),(19,'Nuevo León',1,NULL),(20,'Oaxaca',1,NULL),(21,'Puebla',1,NULL),(22,'Querétaro',1,NULL),(23,'Quintana Roo',1,NULL),(24,'San Luis Potosí',1,NULL),(25,'Sinaloa',1,NULL),(26,'Sonora',1,NULL),(27,'Tabasco',1,NULL),(28,'Tamaulipas',1,NULL),(29,'Tlaxcala',1,NULL),(30,'Veracruz',1,NULL),(31,'Yucatán',1,NULL),(32,'Zacatecas',1,NULL);
/*!40000 ALTER TABLE `estados_mexico` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `materias_primas`
--

LOCK TABLES `materias_primas` WRITE;
/*!40000 ALTER TABLE `materias_primas` DISABLE KEYS */;
INSERT INTO `materias_primas` VALUES (1,'Piel vacuna negra','Cuero para bolsos',4,'2026-04-09 00:09:53','2026-04-09 00:09:53','piel'),(2,'Forro Textil','Interior de bolsos',5,'2026-04-09 00:11:37','2026-04-09 00:11:37','textil'),(3,'Hilo de coser','Hilo resistente',3,'2026-04-09 00:12:11','2026-04-09 00:45:45','hilo'),(4,'Cierres','Cierres',8,'2026-04-09 00:40:13','2026-04-09 00:40:13','accesorio'),(5,'Químicos sólidos','Químicos',7,'2026-04-09 00:41:28','2026-04-09 00:41:28','quimico'),(6,'Químicos líquidos','Químicos',6,'2026-04-09 00:42:39','2026-04-09 00:42:39','quimico');
/*!40000 ALTER TABLE `materias_primas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `movimientos_caja`
--

LOCK TABLES `movimientos_caja` WRITE;
/*!40000 ALTER TABLE `movimientos_caja` DISABLE KEYS */;
INSERT INTO `movimientos_caja` VALUES (1,'SALIDA','Pago OC OC-2026-0001 – Distribuidora de Insumos León',116000.00,NULL,'OC-001',1,NULL,'2026-04-09 00:17:14',1,'Recibida'),(2,'SALIDA','Pago OC OC-2026-0003 – Forros y Telas del Centro',4640.00,NULL,'GI-001',3,NULL,'2026-04-09 00:19:03',1,'Recibida'),(3,'SALIDA','Pago OC OC-2026-0004 – Textiles del Bajío SA de CV',13920.00,NULL,'KI-002',4,NULL,'2026-04-09 00:20:57',1,'Recibida'),(4,'SALIDA','Pago OC OC-2026-0005 – Distribuidora de Insumos León',116.00,NULL,'UF-001',5,NULL,'2026-04-09 00:44:50',1,'Recibido'),(5,'SALIDA','Pago OC OC-2026-0006 – Pieles Finas MX',9280.00,NULL,'GH-002',6,NULL,'2026-04-09 00:48:26',1,'Recibido');
/*!40000 ALTER TABLE `movimientos_caja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `movimientos_materia_prima`
--

LOCK TABLES `movimientos_materia_prima` WRITE;
/*!40000 ALTER TABLE `movimientos_materia_prima` DISABLE KEYS */;
INSERT INTO `movimientos_materia_prima` VALUES (1,2,4,'COMPRA',20.00,5000.00,'OC-2026-0001','2026-04-09 00:17:15'),(2,3,3,'COMPRA',40.00,100.00,'OC-2026-0003','2026-04-09 00:19:03'),(3,1,1,'COMPRA',15.00,800.00,'OC-2026-0004','2026-04-09 00:20:57'),(4,4,4,'COMPRA',100.00,1.00,'OC-2026-0005','2026-04-09 00:44:50'),(5,1,2,'COMPRA',1000.00,8.00,'OC-2026-0006','2026-04-09 00:48:26');
/*!40000 ALTER TABLE `movimientos_materia_prima` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `ordenes_compra`
--

LOCK TABLES `ordenes_compra` WRITE;
/*!40000 ALTER TABLE `ordenes_compra` DISABLE KEYS */;
INSERT INTO `ordenes_compra` VALUES (1,'OC-2026-0001',4,'CONFIRMADA','2026-04-09 00:16:23',116000.00,'Recibida',1,100000.00,16000.00,'OC-001'),(2,'OC-2026-0002',1,'CANCELADA','2026-04-09 00:17:55',87000.00,'Recibida',1,75000.00,12000.00,'KI-001'),(3,'OC-2026-0003',3,'CONFIRMADA','2026-04-09 00:18:21',4640.00,'Recibida',1,4000.00,640.00,'GI-001'),(4,'OC-2026-0004',1,'CONFIRMADA','2026-04-09 00:20:34',13920.00,'Recibida',1,12000.00,1920.00,'KI-002'),(5,'OC-2026-0005',4,'CONFIRMADA','2026-04-09 00:44:31',116.00,'Recibido',1,100.00,16.00,'UF-001'),(6,'OC-2026-0006',2,'CONFIRMADA','2026-04-09 00:47:14',9280.00,'Recibido',1,8000.00,1280.00,'GH-002');
/*!40000 ALTER TABLE `ordenes_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `ordenes_produccion`
--

LOCK TABLES `ordenes_produccion` WRITE;
/*!40000 ALTER TABLE `ordenes_produccion` DISABLE KEYS */;
/*!40000 ALTER TABLE `ordenes_produccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `piezas_materia_prima`
--

LOCK TABLES `piezas_materia_prima` WRITE;
/*!40000 ALTER TABLE `piezas_materia_prima` DISABLE KEYS */;
INSERT INTO `piezas_materia_prima` VALUES (1,2,20.00,1,'2026-04-09 00:17:15',1),(2,1,15.00,1,'2026-04-09 00:20:57',3),(3,1,1000.00,1,'2026-04-09 00:48:26',5);
/*!40000 ALTER TABLE `piezas_materia_prima` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `productos`
--

LOCK TABLES `productos` WRITE;
/*!40000 ALTER TABLE `productos` DISABLE KEYS */;
INSERT INTO `productos` VALUES (1,'MA-LI-532','Maletín \'Caramel\'','Executive','Maletines Empresariales',1500.00,0.00,120.00,0,'WhatsApp_Image_2026-04-08_at_17.34.29.jpeg','2026-04-09 00:52:20'),(2,'MA-LI-538','Maletín \'Expresso\'','Executive','Maletines Empresariales',1600.00,0.00,120.00,0,'WhatsApp_Image_2026-04-08_at_17.34.29_1.jpeg','2026-04-09 00:53:14'),(3,'CA-LI-733','Chamarra \'Mocha\' L','Lifestyle','Chamarras Elite',18000.00,0.00,316.00,0,'WhatsApp_Image_2026-04-08_at_17.34.29_2.jpeg','2026-04-09 00:59:23'),(4,'ELI-FOG-992','Chamarra \'Obsidian\'','Executive','Chamarras Elite',19000.00,0.00,320.00,0,'WhatsApp_Image_2026-04-08_at_17.34.30_1.jpeg','2026-04-09 01:01:20'),(5,'CST-PRC-672','Cinturón \'Stout\'','Essentials','Cinturones Signature',800.00,0.00,40.00,0,'WhatsApp_Image_2026-04-08_at_17.34.30_3.jpeg','2026-04-09 01:02:53'),(6,'DUH-INT-881','Cinturón \'Toffee\'','Essentials','Cinturones Signature',750.00,0.00,40.00,0,'WhatsApp_Image_2026-04-08_at_17.34.30_4.jpeg','2026-04-09 01:04:35'),(7,'BIH-KOC-316','Bolso \'Peony\'','Lifestyle','Bolsos London Bloom',25000.00,0.00,85.00,0,'WhatsApp_Image_2026-04-08_at_17.34.30_5.jpeg','2026-04-09 01:11:02'),(8,'DIH-MAZ-884','Cartera \'Oxford\'','Executive','Cartera Old Money',10000.00,0.00,50.00,0,'WhatsApp_Image_2026-04-08_at_17.34.31.jpeg','2026-04-09 01:13:06'),(9,'CIP-GIN-484','Cartera \'Magallan\'','Executive','Cartera Old Money',9000.00,0.00,50.00,0,'WhatsApp_Image_2026-04-08_at_17.34.30_6.jpeg','2026-04-09 01:14:46'),(10,'FIB-SCM-991','LLavero \'Petit\'','Essentials','Lavero Esenciales',100.00,0.00,2.00,0,'WhatsApp_Image_2026-04-08_at_17.34.31_1.jpeg','2026-04-09 01:17:10');
/*!40000 ALTER TABLE `productos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `proveedores`
--

LOCK TABLES `proveedores` WRITE;
/*!40000 ALTER TABLE `proveedores` DISABLE KEYS */;
INSERT INTO `proveedores` VALUES (1,'Textiles del Bajío SA de CV','Carlos López','4491234567','ventas@textilesbajio.com','TBA010101AAA','Av. Industria 123','Aguascalientes','Proveedor principal de piel',1,'2026-04-09 00:07:24','2026-04-09 00:07:24',1,NULL),(2,'Pieles Finas MX','Ana Martínez','3312345678','contacto@pielesfinas.com','PFM020202BBB','Calle Curtidores 456','Guadalajara','Alta calidad en cuero',2,'2026-04-09 00:07:24','2026-04-09 00:07:24',1,NULL),(3,'Forros y Telas del Centro','Luis Hernández','5556781234','ventas@forroscentro.com','FTC030303CCC','Calle Textil 789','CDMX','Especialistas en forros',3,'2026-04-09 00:07:24','2026-04-09 00:07:24',1,NULL),(4,'Distribuidora de Insumos León','María Gómez','4779876543','contacto@insumosleon.com','DIL040404DDD','Blvd. Piel 321','León','Venta de materiales varios',2,'2026-04-09 00:07:24','2026-04-09 00:07:24',1,NULL),(5,'Hilos Industriales del Norte','Pedro Ramírez','8182345678','ventas@hilosnorte.com','HIN050505EEE','Av. Industria Textil 654','Monterrey','Proveedor de hilos resistentes',2,'2026-04-09 00:07:24','2026-04-09 00:07:24',1,NULL);
/*!40000 ALTER TABLE `proveedores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `recetas`
--

LOCK TABLES `recetas` WRITE;
/*!40000 ALTER TABLE `recetas` DISABLE KEYS */;
INSERT INTO `recetas` VALUES (1,1,1,120.00,130.00),(2,1,2,0.00,2.00),(3,1,3,0.00,2.00),(4,1,6,0.00,1.00),(5,3,1,316.00,240.00),(6,3,2,0.00,4.00),(7,3,3,0.00,4.00),(8,3,6,0.00,2.00),(9,3,4,0.00,1.00),(10,7,1,85.00,60.00),(11,7,2,0.00,1.00),(12,7,3,0.00,1.00),(13,7,6,0.00,1.00),(14,7,4,0.00,1.00);
/*!40000 ALTER TABLE `recetas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `retales_recuperados`
--

LOCK TABLES `retales_recuperados` WRITE;
/*!40000 ALTER TABLE `retales_recuperados` DISABLE KEYS */;
/*!40000 ALTER TABLE `retales_recuperados` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'Admin','Acceso para Admin'),(2,'Artesano','Acceso para Artesano'),(3,'Cliente','Acceso para Cliente');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `stock_materia_prima`
--

LOCK TABLES `stock_materia_prima` WRITE;
/*!40000 ALTER TABLE `stock_materia_prima` DISABLE KEYS */;
INSERT INTO `stock_materia_prima` VALUES (1,2.00,0.00,'2026-04-09 00:48:26'),(2,1.00,0.00,'2026-04-09 00:17:15'),(3,40.00,0.00,'2026-04-09 00:19:03'),(4,100.00,0.00,'2026-04-09 00:44:50'),(5,0.00,0.00,'2026-04-09 00:41:28'),(6,0.00,0.00,'2026-04-09 00:42:39');
/*!40000 ALTER TABLE `stock_materia_prima` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `unidades_medida`
--

LOCK TABLES `unidades_medida` WRITE;
/*!40000 ALTER TABLE `unidades_medida` DISABLE KEYS */;
INSERT INTO `unidades_medida` VALUES (3,'Metros','m','hilo','2026-04-08 23:48:13'),(4,'Decimetro cuadrado','dm²','piel','2026-04-08 23:48:40'),(5,'Metro cuadrado','m²','textil','2026-04-08 23:49:08'),(6,'Líquidos químicos','L','quimico','2026-04-08 23:49:41'),(7,'Químicos sólidos','Kg','quimico','2026-04-08 23:50:44'),(8,'Herrajes y piezas','pz','accesorio','2026-04-08 23:52:52');
/*!40000 ALTER TABLE `unidades_medida` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'admin_majo','scrypt:32768:8:1$QLxRcasB9JHJhsj6$40f94b699d7caa06eaeb40339e482c3c62cfb2d56b1ba8b277d925497c192487cf37a77b88d107a371c3ebc97a742bfb3ba4943381be3e840dfbe3c2a76c6a4a',0,0,1),(2,'maint_ange','scrypt:32768:8:1$5RispK2o6OpKZcN6$b7f5db3d8ce51278de5efe5b15f6b756cc3af5686f7ab4eea1bcd68d69a00c762b7a2ff40becb96c74f2b087494da3ace498e9f540ffd8d25237b8880974e4f9',0,0,1),(3,'user_emilio','scrypt:32768:8:1$rzRR3uRgrGbHHYvj$0acc2a728ebb7f35ae56a0e36df839ecc114892b0348dd2666fe4a39e81b2662995725c3ed0936cc4074eea940705aae8af207c94222866a88cb1b9c4bef5cb6',0,0,1),(4,'maint_diego','scrypt:32768:8:1$pnZzGNnEm9vFdDOG$02e49076ee7d5a5c42141e5fdf29a08a4143f8016263a3392777239800920f957ea0fcb50c141395ca4c87418ff2ec7ebad9cbca99462242d5189898e123dc61',0,0,1),(5,'cliente_test','scrypt:32768:8:1$M8ZpF8dEA0Fe8jak$85248c2901e65b6314cd778aee5c5e7ea1e5bba47e61a028ab8fcb2f75c953179bccf5ea62db92faa0b8992529e6b37cdb14889a36bda226bb04e618423129f2',0,0,3),(6,'angel_cliente','scrypt:32768:8:1$5ndYXulTBqscbMcS$700e1b5c1695d9d303ffab2b8aae528e7ead7daaf37a82e8135b3296c83715d301d47243feddfee83d865fc75f9fcb9af23b9408183efe4d43c4f6c712ba3b49',0,0,3),(7,'majo_cliente','scrypt:32768:8:1$JEo9u5rT1OFamgXe$485466d42673f948232e2a88b38df5429f47240ab4e970db7b56e01d5413c088bcfcbf11a9559a67bb21f8c1619e713d86874330e5367fea8eacdb2c41877808',0,0,3);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `ventas`
--

LOCK TABLES `ventas` WRITE;
/*!40000 ALTER TABLE `ventas` DISABLE KEYS */;
/*!40000 ALTER TABLE `ventas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'vellum_db'
--

--
-- Dumping routines for database 'vellum_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-08 19:43:01
