<?php

interface MenuPilihan {
    public function tambahPengiriman($item);
    public function tampilkanPengiriman();
}

abstract class JenisPengiriman implements MenuPilihan {
    private $nama;
    private $harga;
    private $daftar = array();
    private $totalBerat = 0;
    private $km = 0;

    private function getNamaBarang() {
        $nama = array_map(function($item) {
            return $item['nama'];
        }, $this->daftar);
        return implode(", ", $nama);
    }

    public function __construct($nama, $harga, $km) {
        $this->nama = $nama;
        $this->harga = $harga;
        $this->km = $km;
    }
    
    public function tambahPengiriman($item) {
        $this->daftar[] = $item;
        $this->totalBerat += $item['berat'];
        return true;
    }
    
    public function tampilkanPengiriman() {
        $namaBarang = $this->getNamaBarang();
        $biaya = number_format($this->hitungBiaya());
        
        echo "Paket: " . $this->nama . "\n";
        echo "Barang: " . $namaBarang . "\n";
        echo "Berat: " . $this->totalBerat . " kg\n";
        echo "Jarak: " . $this->km . " km\n";
        echo "Estimasi: ~" . $this->hitungEstimasi() . " hari\n";
        echo "Biaya: Rp " . $biaya . "\n\n";
    }
    
    public function getNama() {
        return $this->nama;
    }

    public function getTotalBerat() {
        return $this->totalBerat;
    }
    
    public function getHarga() {
        return $this->harga;
    }
    
    public function getKm() {
        return $this->km;
    }

    abstract public function hitungBiaya();
    
    abstract public function hitungEstimasi();
}

class JenisReguler extends JenisPengiriman {
    private function hitungBiayaKm() {
        $km = $this->getKm();
        if ($km <= 10) {
            return 0;
        }
        $kmTambahan = $km - 10;
        $biayaTambahan = ceil($kmTambahan / 10);
        return $biayaTambahan * 2000;
    }

    public function __construct($km) {
        parent::__construct("Reguler", 5000, $km);
    }
        
    public function hitungBiaya() {
        $biayaBerat = $this->getTotalBerat() * $this->getHarga();
        $biayaKm = $this->hitungBiayaKm();
        return $biayaBerat + $biayaKm;
    }
    
    public function hitungEstimasi() {
        $km = $this->getKm();
        $hari = 4;
        if ($km >= 60) {
            $hari += ceil($km / 60);
        }
        return $hari;
    }
}

class JenisFasttrack extends JenisPengiriman {
    private $layanan = 10000;
    
    private function hitungBiayaKm() {
        $km = $this->getKm();
        if ($km <= 10) {
            return 0;
        }
        $kmTambahan = $km - 10;
        $biayaTambahan = ceil($kmTambahan / 10);
        return $biayaTambahan * 2500;
    }

    public function __construct($km) {
        parent::__construct("Fasttrack", 7500, $km);
    }
    
    public function hitungBiaya() {
        $biayaBerat = $this->getTotalBerat() * $this->getHarga();
        $biayaKm = $this->hitungBiayaKm();
        return $biayaBerat + $this->layanan + $biayaKm;
    }
    
    public function hitungEstimasi() {
        $km = $this->getKm();
        $hari = 2;
        if ($km >= 60) {
            $hari += ceil($km / 80);
        }
        return $hari;
    }
}

class JenisKargo extends JenisPengiriman {
    private $min = 10;
    private function hitungBiayaKm() {
        $km = $this->getKm();
        if ($km <= 100) {
            return 0;
        }
        $kmTambahan = $km - 100;
        $biayaTambahan = ceil($kmTambahan / 10);
        return $biayaTambahan * 2000;
    }

    public function __construct($km) {
        parent::__construct("Kargo", 3000, $km);
    }
    
    public function hitungBiaya() {
        if ($this->getTotalBerat() >= $this->min) {
            $biayaBerat = $this->getTotalBerat() * $this->getHarga();
            $biayaKm = $this->hitungBiayaKm();
        }
        return $biayaBerat + $biayaKm;
    }
    
    public function hitungEstimasi() {
        $km = $this->getKm();
        $hari = 6;
        if ($km >= 60) {
            $hari += ceil($km / 40);
        }
        return $hari;
    }
}
?>
    