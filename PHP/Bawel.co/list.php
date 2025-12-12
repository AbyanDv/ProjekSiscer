<?php
require_once 'Gebleg.php';

function buatObjekPengiriman($jenisPaket, $jarak) {
    if ($jenisPaket === 'Reguler') {
        return new JenisReguler($jarak);
    } elseif ($jenisPaket === 'Fasttrack') {
        return new JenisFasttrack($jarak);
    } elseif ($jenisPaket === 'Kargo') {
        return new JenisKargo($jarak);
    }
    return null;
}

function bacaDataJson($file) {
    if (!file_exists($file)) {
        return array();
    }
    $isi = file_get_contents($file);
    $data = json_decode($isi, true);
    return ($data === null) ? array() : $data;
}

$jsonFile = 'data.json';
$data = bacaDataJson($jsonFile);

$editIndex = null;
$editData = null;
$editError = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['aksi'])) {
    $aksi = $_POST['aksi'];
    
    if ($aksi === 'hapus') {
        $index = intval($_POST['index']);
        if (isset($data[$index])) {
            unset($data[$index]);
            $data = array_values($data);
            file_put_contents($jsonFile, json_encode($data, JSON_PRETTY_PRINT));
        }
        header('Location: list.php');
        exit;
    }
    
    if ($aksi === 'edit') {
        $editIndex = intval($_POST['index']);
        if (isset($data[$editIndex])) {
            $editData = $data[$editIndex];
        }
    }
    
    if ($aksi === 'simpan_edit') {
        $editIndex = intval($_POST['index']);
        $jenisBaru = $_POST['jenis'];
        $beratBaru = intval($_POST['berat']);
        $jarakBaru = intval($_POST['jarak']);
        
        $errorList = array();
        
        if ($jarakBaru < 5) {
            $errorList[] = "Jarak minimal 5km!";
        }
        if ($beratBaru > 500) {
            $errorList[] = "Berat maksimum 500kg!";
        }
        if ($jarakBaru > 1500) {
            $errorList[] = "Jarak maksimum 1500km!";
        }
        if ($jenisBaru === 'Kargo' && $beratBaru < 10) {
            $errorList[] = "Kargo memerlukan minimum berat 10kg!";
        }
        
        if (!empty($errorList)) {
            $editData = array(
                'jenis' => $jenisBaru,
                'nama_barang' => $_POST['nama_barang'],
                'berat' => $beratBaru,
                'jarak' => $jarakBaru
            );
            $editError = implode(" | ", $errorList);
        } elseif (isset($data[$editIndex])) {
            $data[$editIndex]['jenis'] = $jenisBaru;
            $data[$editIndex]['nama_barang'] = $_POST['nama_barang'];
            $data[$editIndex]['berat'] = $beratBaru;
            $data[$editIndex]['jarak'] = $jarakBaru;
            file_put_contents($jsonFile, json_encode($data, JSON_PRETTY_PRINT));
            header('Location: list.php');
            exit;
        }
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Daftar Pengiriman</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

<h1>Daftar Pengiriman</h1>

<a href="index.php"><button class="btn-add">Kembali</button></a>

<h2>Data Pengiriman</h2>

<?php if ($editData !== null): ?>
    <div style="background-color: #e8f4f8; padding: 20px; margin-bottom: 20px; border-left: 4px solid #0066cc;">
        <h3>Edit Data</h3>
        
        <?php if ($editError !== null): ?>
            <div style="background-color: #ffcccc; padding: 10px; margin: 10px 0; border: 1px solid #ff0000; color: #cc0000;">
                <?php echo $editError; ?>
            </div>
        <?php endif; ?>
        
        <form method="POST">
            <input type="hidden" name="aksi" value="simpan_edit">
            <input type="hidden" name="index" value="<?php echo $editIndex; ?>">
            
            <label>Jenis Paket:</label>
            <select name="jenis" required>
                <option value="Reguler" <?php if ($editData['jenis'] === 'Reguler') echo 'selected'; ?>>Reguler</option>
                <option value="Fasttrack" <?php if ($editData['jenis'] === 'Fasttrack') echo 'selected'; ?>>Fasttrack</option>
                <option value="Kargo" <?php if ($editData['jenis'] === 'Kargo') echo 'selected'; ?>>Kargo</option>
            </select>
            
            <label>Nama Barang:</label>
            <input type="text" name="nama_barang" value="<?php echo htmlspecialchars($editData['nama_barang']); ?>" required>
            
            <label>Berat (kg):</label>
            <input type="number" name="berat" value="<?php echo $editData['berat']; ?>" required>
            
            <label>Jarak (km):</label>
            <input type="number" name="jarak" value="<?php echo $editData['jarak']; ?>" required>
            
            <button type="submit" class="btn-add">Simpan Perubahan</button>
            <a href="list.php"><button type="button" class="btn-reset">Batal</button></a>
        </form>
    </div>
<?php endif; ?>

<?php if (empty($data)): ?>
    <div class="empty">Belum ada pengiriman</div>
<?php else: ?>
    <table>
        <tr>
            <th>Tanggal</th>
            <th>Paket</th>
            <th>Barang</th>
            <th>Berat</th>
            <th>Jarak</th>
            <th>Estimasi</th>
            <th>Biaya</th>
            <th>Aksi</th>
        </tr>
        
        <?php foreach ($data as $index => $item): ?>
            <?php 
                $objek = buatObjekPengiriman($item['jenis'], $item['jarak']);
                
                if ($objek !== null) {
                    $objek->tambahPengiriman(array(
                        'nama' => $item['nama_barang'],
                        'berat' => $item['berat']
                    ));
                }
                
                $tanggal = isset($item['tanggal']) ? $item['tanggal'] : date('d/m/Y');
            ?>
            
            <tr>
                <td><?php echo $tanggal; ?></td>
                <td><?php echo $item['jenis']; ?></td>
                <td><?php echo $item['nama_barang']; ?></td>
                <td><?php echo $item['berat']; ?> kg</td>
                <td><?php echo $item['jarak']; ?> km</td>
                <td>~<?php echo $objek->hitungEstimasi(); ?> hari</td>
                <td>Rp <?php echo number_format($objek->hitungBiaya()); ?></td>
                <td>
                    <form method="POST" style="display:inline;">
                        <input type="hidden" name="aksi" value="edit">
                        <input type="hidden" name="index" value="<?php echo $index; ?>">
                        <button type="submit" class="btn-edit">Edit</button>
                    </form>
                    <form method="POST" style="display:inline;">
                        <input type="hidden" name="aksi" value="hapus">
                        <input type="hidden" name="index" value="<?php echo $index; ?>">
                        <button type="submit" class="btn-delete" onclick="return confirm('Yakin?')">Hapus</button>
                    </form>
                </td>
            </tr>
        <?php endforeach; ?>
    </table
<?php endif; ?>
</body>
</html>