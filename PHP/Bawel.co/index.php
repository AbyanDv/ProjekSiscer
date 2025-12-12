<?php
require_once 'Gebleg.php';

$error = null;
$success = null;

function bacaDataJson($file) {
    if (!file_exists($file)) {
        return array();
    }
    $isi = file_get_contents($file);
    $data = json_decode($isi, true);
    return ($data === null) ? array() : $data;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['aksi'])) {
    $aksi = $_POST['aksi'];
    
    if ($aksi === 'tambah') {
        $jenisPaket = $_POST['jenis_paket'];
        $namaBarang = $_POST['nama_barang'];
        $berat = floatval($_POST['berat']);
        $jarak = intval($_POST['jarak']);
        
        $errorList = array();
        
        if ($jarak < 5) {
            $errorList[] = "Jarak minimal 5km!";
        }
        if ($berat > 500) {
            $errorList[] = "Berat maksimum 500kg!";
        }
        if ($jarak > 1500) {
            $errorList[] = "Jarak maksimum 1500km!";
        }
        if ($jenisPaket === 'Kargo' && $berat < 10) {
            $errorList[] = "Kargo memerlukan minimum berat 10kg!";
        }
        
        if (!empty($errorList)) {
            $error = implode(" | ", $errorList);
        } else {
            $jsonFile = 'data.json';
            $data = bacaDataJson($jsonFile);
            
            $data[] = array(
                'jenis' => $jenisPaket,
                'nama_barang' => $namaBarang,
                'berat' => $berat,
                'jarak' => $jarak,
                'tanggal' => date('d/m/Y')
            );
            
            file_put_contents($jsonFile, json_encode($data, JSON_PRETTY_PRINT));
            $success = "Pengiriman berhasil ditambahkan!";
        }
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sistem Pengiriman</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

<h1>Sistem Pengiriman Paket</h1>

<?php if (isset($error)): ?>
    <div style="background-color: #ffcccc; padding: 10px; margin: 10px 0; border: 1px solid #ff0000; color: #cc0000;">
        <?php echo $error; ?>
    </div>
<?php endif; ?>

<?php if (isset($success)): ?>
    <div style="background-color: #ccffcc; padding: 10px; margin: 10px 0; border: 1px solid #00cc00; color: #006600;">
        <?php echo $success; ?>
    </div>
<?php endif; ?>

<h2>Form Tambah Pengiriman</h2>
<form method="POST">
    <div>
        <label>Jenis Paket:</label><br>
        <select name="jenis_paket" required>
            <option value="">Pilih</option>
            <option value="Reguler">Reguler</option>
            <option value="Fasttrack">Fasttrack</option>
            <option value="Kargo">Kargo (min 10kg)</option>
        </select>
    </div>

    <div>
        <label>Nama Barang:</label><br>
        <input type="text" name="nama_barang" required>
    </div>

    <div>
        <label>Berat (kg):</label><br>
        <input type="number" name="berat" step="0.1" required>
    </div>

    <div>
        <label>Jarak (km):</label><br>
        <input type="number" name="jarak" required>
    </div>

    <input type="hidden" name="aksi" value="tambah">
    <button type="submit" class="btn-add">Tambah Pengiriman</button>
</form>

<br>
<a href="list.php"><button class="btn-add">List Pengiriman</button></a>

</body>
</html>
