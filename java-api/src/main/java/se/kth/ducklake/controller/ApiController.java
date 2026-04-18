package se.kth.ducklake.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import se.kth.ducklake.model.*;
import se.kth.ducklake.service.DuckLakeService;

import java.util.List;
import java.util.Map;

@RestController
public class ApiController {

    private final DuckLakeService lake;

    @Value("${ducklake.api.key}")
    private String apiKey;

    public ApiController(DuckLakeService lake) {
        this.lake = lake;
    }

    private ResponseEntity<Map<String, String>> unauthorized() {
        return ResponseEntity.status(401).body(Map.of("detail", "Ogiltig API-nyckel"));
    }

    private boolean validKey(String key) {
        return key != null && key.equals(apiKey);
    }

    // ── HEALTH ────────────────────────────────────────────────────────────────

    @GetMapping("/healthz")
    public Map<String, String> health() {
        return Map.of("status", "ok");
    }

    // ── KUNDER ────────────────────────────────────────────────────────────────

    @GetMapping("/api/kunder")
    public List<Map<String, Object>> getKunder() throws Exception {
        return lake.query("SELECT id, namn, email, telefon FROM lake.kunder ORDER BY id");
    }

    @PostMapping("/api/kunder")
    public ResponseEntity<?> nyKund(@RequestHeader(value = "X-API-Key", required = false) String key,
                                     @RequestBody NyKund kund) throws Exception {
        if (!validKey(key)) return unauthorized();
        int nid = ((Number) lake.scalar("SELECT COALESCE(MAX(id),0)+1 FROM lake.kunder")).intValue();
        lake.update("INSERT INTO lake.kunder VALUES (?,?,?,?)", nid, kund.namn(), kund.email(), kund.telefon());
        return ResponseEntity.status(201).body(Map.of("id", nid, "namn", kund.namn(), "email", kund.email()));
    }

    @DeleteMapping("/api/kunder/{id}")
    public ResponseEntity<?> raderaKund(@PathVariable int id,
                                         @RequestHeader(value = "X-API-Key", required = false) String key) throws Exception {
        if (!validKey(key)) return unauthorized();
        lake.update("DELETE FROM lake.kunder WHERE id = ?", id);
        return ResponseEntity.ok(Map.of("deleted", id));
    }

    // ── PRODUKTER ─────────────────────────────────────────────────────────────

    @GetMapping("/api/produkter")
    public List<Map<String, Object>> getProdukt() throws Exception {
        return lake.query("SELECT id, namn, pris, lagersaldo FROM lake.produkter ORDER BY id");
    }

    @PostMapping("/api/produkter")
    public ResponseEntity<?> nyProdukt(@RequestHeader(value = "X-API-Key", required = false) String key,
                                        @RequestBody NyProdukt p) throws Exception {
        if (!validKey(key)) return unauthorized();
        int nid = ((Number) lake.scalar("SELECT COALESCE(MAX(id),0)+1 FROM lake.produkter")).intValue();
        lake.update("INSERT INTO lake.produkter VALUES (?,?,?,?)", nid, p.namn(), p.pris(), p.lagersaldo() != null ? p.lagersaldo() : 0);
        return ResponseEntity.status(201).body(Map.of("id", nid, "namn", p.namn(), "pris", p.pris()));
    }

    @DeleteMapping("/api/produkter/{id}")
    public ResponseEntity<?> raderaProdukt(@PathVariable int id,
                                            @RequestHeader(value = "X-API-Key", required = false) String key) throws Exception {
        if (!validKey(key)) return unauthorized();
        lake.update("DELETE FROM lake.produkter WHERE id = ?", id);
        return ResponseEntity.ok(Map.of("deleted", id));
    }

    // ── ORDRAR ────────────────────────────────────────────────────────────────

    @GetMapping("/api/ordrar")
    public List<Map<String, Object>> getOrdrar() throws Exception {
        return lake.query("""
            SELECT o.id, k.namn AS kund, p.namn AS produkt, o.antal, o.skapad
            FROM lake.ordrar o
            JOIN lake.kunder k    ON k.id = o.kund_id
            JOIN lake.produkter p ON p.id = o.produkt_id
            ORDER BY o.id
            """);
    }

    @PostMapping("/api/ordrar")
    public ResponseEntity<?> nyOrder(@RequestHeader(value = "X-API-Key", required = false) String key,
                                      @RequestBody NyOrder o) throws Exception {
        if (!validKey(key)) return unauthorized();
        int nid = ((Number) lake.scalar("SELECT COALESCE(MAX(id),0)+1 FROM lake.ordrar")).intValue();
        lake.update("INSERT INTO lake.ordrar (id,kund_id,produkt_id,antal) VALUES (?,?,?,?)",
                nid, o.kund_id(), o.produkt_id(), o.antal());
        return ResponseEntity.status(201).body(Map.of("id", nid));
    }

    // ── DATASETS ──────────────────────────────────────────────────────────────

    @GetMapping("/api/datasets")
    public List<Map<String, Object>> getDatasets() throws Exception {
        return lake.query("SELECT table_name FROM duckdb_tables() WHERE database_name = 'lake'");
    }

    @GetMapping("/api/datasets/{namn}")
    public ResponseEntity<?> getDataset(@PathVariable String namn) throws Exception {
        List<Map<String, Object>> tabeller = lake.query(
            "SELECT table_name FROM duckdb_tables() WHERE database_name = 'lake' AND table_name = ?", namn);
        if (tabeller.isEmpty())
            return ResponseEntity.status(404).body(Map.of("detail", "Dataset '" + namn + "' hittades inte"));
        List<Map<String, Object>> data = lake.query("SELECT * FROM lake." + namn + " LIMIT 100");
        return ResponseEntity.ok(Map.of("namn", namn, "antal_rader", data.size(), "data", data));
    }
}
