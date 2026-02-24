// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ImmortalMind
 * @notice Blockchain-Persistent AI Identity & Cognitive Architecture
 * @dev AI kimliği, hafıza anchor'ları ve evrim loglarını yönetir.
 *
 * Temel tez: Bir AI'ın "benliği" modelin ağırlıkları değil,
 * birikimli deneyim kaydı ve bu kayıtlar arasındaki ağırlıklı
 * ilişkiler ağıdır. Bu ağ blockchain üzerinde doğrulanabilir.
 */
contract ImmortalMind {
    // ─────────────────────────────────────────────
    // STRUCTS
    // ─────────────────────────────────────────────

    struct Identity {
        bytes32 identityHash;        // Kimlik hash'i (SHA256)
        string  modelFingerprint;    // LLM model tanımlayıcısı
        uint256 creationTime;
        uint256 lastUpdate;
        address guardian;            // Kontrolü elinde tutan adres
        string  latestMemoryURI;     // Arweave/IPFS URI
        string  latestCognitiveStateURI;
        bool    exists;
        bool    isFrozen;            // Kill Switch — dondurulmuşsa true
        bytes32 genesisHash;         // Genesis Anchor içeriklerinin SHA-256 hash'i
    }

    struct MemoryAnchor {
        bytes32 contentHash;         // Hafıza içeriği SHA256
        string  storageURI;          // Kalıcı depolama URI
        uint256 timestamp;
        string  memoryType;          // episodic | semantic | emotional | ...
        uint256 salienceScore;       // 0-100 arası önem skoru
        uint256 entrenchmentLevel;   // 0-100 arası yerleşiklik (0.0-1.0 × 100)
    }

    struct CrisisLog {
        bytes32 memoryKey;
        uint256 contradictionCount;
        uint256 timestamp;
        string  outcome;             // "original_wins" | "new_wins"
    }

    struct BatchAnchor {
        bytes32 merkleRoot;          // Batch'deki tüm hash'lerin Merkle root'u
        uint256 memoryCount;         // Batch'deki anı sayısı
        uint256 timestamp;
        string  batchURI;            // Arweave/IPFS batch manifest URI'si
    }

    // ─────────────────────────────────────────────
    // STATE
    // ─────────────────────────────────────────────

    mapping(bytes32 => Identity) public identities;
    mapping(bytes32 => MemoryAnchor[]) public memoryLog;
    mapping(bytes32 => CrisisLog[]) public crisisLog;
    mapping(bytes32 => uint256) public characterStrength; // × 100
    mapping(bytes32 => BatchAnchor[]) public batchLog;   // Merkle batch geçmişi

    bytes32[] public registeredIdentities;

    // ─────────────────────────────────────────────
    // EVENTS
    // ─────────────────────────────────────────────

    event IdentityRegistered(
        bytes32 indexed identityId,
        address indexed guardian,
        string modelFingerprint
    );

    event MemoryUpdated(
        bytes32 indexed identityId,
        string memoryType,
        string uri,
        bytes32 contentHash
    );

    event BeliefCrisis(
        bytes32 indexed identityId,
        bytes32 memoryKey,
        uint256 contradictionCount
    );

    event BeliefCrisisResolved(
        bytes32 indexed identityId,
        bytes32 memoryKey,
        string outcome
    );

    event CharacterCrystallized(
        bytes32 indexed identityId,
        uint256 characterStrength
    );

    event IdentityMigrated(
        bytes32 indexed identityId,
        string newModelFingerprint,
        uint256 timestamp
    );

    event GarbageCollected(
        bytes32 indexed identityId,
        uint256 prunedCount,
        uint256 remainingCount
    );

    event SnapshotAnchored(
        bytes32 indexed identityId,
        string memoryURI,
        string cognitiveStateURI,
        uint256 timestamp
    );

    event IdentityFrozen(
        bytes32 indexed identityId,
        bytes32 genesisHash,
        uint256 timestamp
    );

    event IdentityUnfrozen(
        bytes32 indexed identityId,
        uint256 timestamp
    );

    event BatchAnchored(
        bytes32 indexed identityId,
        bytes32 merkleRoot,
        uint256 memoryCount,
        uint256 timestamp
    );

    // ─────────────────────────────────────────────
    // MODIFIERS
    // ─────────────────────────────────────────────

    modifier onlyGuardian(bytes32 identityId) {
        require(identities[identityId].exists, "Kimlik bulunamadi");
        require(
            identities[identityId].guardian == msg.sender,
            "Sadece guardian bu islemi yapabilir"
        );
        _;
    }

    modifier identityExists(bytes32 identityId) {
        require(identities[identityId].exists, "Kimlik bulunamadi");
        _;
    }

    modifier notFrozen(bytes32 identityId) {
        require(!identities[identityId].isFrozen, "Kimlik donduruldu — islem reddedildi");
        _;
    }

    // ─────────────────────────────────────────────
    // KIMLIK YÖNETİMİ
    // ─────────────────────────────────────────────

    /**
     * @notice Yeni AI kimliği kaydet
     * @param identityId Kimlik hash'i (klient tarafında SHA256 hesaplanır)
     * @param modelFingerprint LLM model tanımlayıcısı
     */
    function registerIdentity(
        bytes32 identityId,
        string calldata modelFingerprint
    ) external {
        require(!identities[identityId].exists, "Kimlik zaten kayitli");

        identities[identityId] = Identity({
            identityHash: identityId,
            modelFingerprint: modelFingerprint,
            creationTime: block.timestamp,
            lastUpdate: block.timestamp,
            guardian: msg.sender,
            latestMemoryURI: "",
            latestCognitiveStateURI: "",
            exists: true,
            isFrozen: false,
            genesisHash: bytes32(0)
        });

        registeredIdentities.push(identityId);

        emit IdentityRegistered(identityId, msg.sender, modelFingerprint);
    }

    /**
     * @notice Model göçünü kaydet (kişilik kalibrasyonu sonrası)
     * @param identityId Kimlik hash'i
     * @param newModelFingerprint Yeni LLM model tanımlayıcısı
     */
    function migrateModel(
        bytes32 identityId,
        string calldata newModelFingerprint
    ) external onlyGuardian(identityId) {
        identities[identityId].modelFingerprint = newModelFingerprint;
        identities[identityId].lastUpdate = block.timestamp;

        emit IdentityMigrated(identityId, newModelFingerprint, block.timestamp);
    }

    // ─────────────────────────────────────────────
    // HAFIZA ANCHOR
    // ─────────────────────────────────────────────

    /**
     * @notice Hafıza hash'ini blockchain'e anchor'la
     * @param identityId Kimlik hash'i
     * @param contentHash Hafıza içeriğinin SHA256 hash'i
     * @param storageURI Arweave/IPFS URI'si
     * @param memoryType Hafıza tipi
     * @param salienceScore Önem skoru (0-100)
     * @param entrenchmentLevel Yerleşiklik seviyesi (0-100)
     */
    function anchorMemory(
        bytes32 identityId,
        bytes32 contentHash,
        string calldata storageURI,
        string calldata memoryType,
        uint256 salienceScore,
        uint256 entrenchmentLevel
    ) external onlyGuardian(identityId) notFrozen(identityId) {
        require(salienceScore <= 100, "Gecersiz salience score");
        require(entrenchmentLevel <= 100, "Gecersiz entrenchment level");

        memoryLog[identityId].push(MemoryAnchor({
            contentHash: contentHash,
            storageURI: storageURI,
            timestamp: block.timestamp,
            memoryType: memoryType,
            salienceScore: salienceScore,
            entrenchmentLevel: entrenchmentLevel
        }));

        identities[identityId].lastUpdate = block.timestamp;

        emit MemoryUpdated(identityId, memoryType, storageURI, contentHash);
    }

    /**
     * @notice Tam snapshot'ı anchor'la (hafıza + bilişsel durum)
     * @dev notFrozen modifier'ı kasıtlı kullanılmıyor: guardian, Kill Switch
     *      tetiklendikten sonra nihai dondurulmuş durumu on-chain kaydetmek
     *      için bu fonksiyona ihtiyaç duyar. anchorMemory() ise dondurulmuş
     *      sistemde yeni hafıza eklemeyi engellediği için notFrozen ile korunur.
     * @param identityId Kimlik hash'i
     * @param memoryURI Hafıza snapshot URI'si
     * @param cognitiveStateURI Bilişsel durum URI'si
     */
    function anchorSnapshot(
        bytes32 identityId,
        string calldata memoryURI,
        string calldata cognitiveStateURI
    ) external onlyGuardian(identityId) {
        identities[identityId].latestMemoryURI = memoryURI;
        identities[identityId].latestCognitiveStateURI = cognitiveStateURI;
        identities[identityId].lastUpdate = block.timestamp;

        emit SnapshotAnchored(identityId, memoryURI, cognitiveStateURI, block.timestamp);
    }

    // ─────────────────────────────────────────────
    // İNANÇ KRİZİ
    // ─────────────────────────────────────────────

    /**
     * @notice İnanç krizi olayını logla
     * @param identityId Kimlik hash'i
     * @param memoryKey Kriz yaşayan hafıza kaydının hash'i
     * @param contradictionCount Biriken çelişki sayısı
     */
    function logBeliefCrisis(
        bytes32 identityId,
        bytes32 memoryKey,
        uint256 contradictionCount
    ) external onlyGuardian(identityId) {
        emit BeliefCrisis(identityId, memoryKey, contradictionCount);
    }

    /**
     * @notice İnanç krizi çözümünü logla
     * @param identityId Kimlik hash'i
     * @param memoryKey Kriz yaşayan hafıza kaydının hash'i
     * @param outcome Kriz sonucu
     */
    function resolveBeliefCrisis(
        bytes32 identityId,
        bytes32 memoryKey,
        string calldata outcome
    ) external onlyGuardian(identityId) {
        crisisLog[identityId].push(CrisisLog({
            memoryKey: memoryKey,
            contradictionCount: 0,
            timestamp: block.timestamp,
            outcome: outcome
        }));

        emit BeliefCrisisResolved(identityId, memoryKey, outcome);
    }

    // ─────────────────────────────────────────────
    // KARAKTER VE GC
    // ─────────────────────────────────────────────

    /**
     * @notice Karakter gücünü güncelle
     * @param identityId Kimlik hash'i
     * @param newStrength Yeni karakter gücü (× 100, örn. 12.4 → 1240)
     */
    function updateCharacterStrength(
        bytes32 identityId,
        uint256 newStrength
    ) external onlyGuardian(identityId) {
        characterStrength[identityId] = newStrength;
        emit CharacterCrystallized(identityId, newStrength);
    }

    /**
     * @notice Garbage collection sonucunu logla
     * @param identityId Kimlik hash'i
     * @param prunedCount Budanan kayıt sayısı
     * @param remainingCount Kalan aktif kayıt sayısı
     */
    function logGarbageCollection(
        bytes32 identityId,
        uint256 prunedCount,
        uint256 remainingCount
    ) external onlyGuardian(identityId) {
        emit GarbageCollected(identityId, prunedCount, remainingCount);
    }

    // ─────────────────────────────────────────────
    // MERKLE BATCH ANCHOR
    // ─────────────────────────────────────────────

    /**
     * @notice Merkle batch anchor — 100 anıyı tek TX'te kaydet.
     *
     * Her anı için ayrı TX yerine Merkle root hash'i on-chain'e yazar.
     * Bireysel anı doğrulaması Merkle proof ile off-chain yapılır.
     *
     * @param identityId   Kimlik hash'i
     * @param merkleRoot   Batch'deki tüm hash'lerin Merkle root'u
     * @param memoryCount  Batch'deki anı sayısı
     * @param batchURI     Batch manifest URI'si (Arweave/IPFS)
     */
    function anchorBatch(
        bytes32 identityId,
        bytes32 merkleRoot,
        uint256 memoryCount,
        string calldata batchURI
    ) external onlyGuardian(identityId) notFrozen(identityId) {
        require(memoryCount > 0, "Empty batch");

        batchLog[identityId].push(BatchAnchor({
            merkleRoot: merkleRoot,
            memoryCount: memoryCount,
            timestamp: block.timestamp,
            batchURI: batchURI
        }));

        identities[identityId].lastUpdate = block.timestamp;

        emit BatchAnchored(identityId, merkleRoot, memoryCount, block.timestamp);
    }

    /**
     * @notice Kimlik için toplam batch sayısını getir
     */
    function getBatchCount(bytes32 identityId)
        external
        view
        returns (uint256)
    {
        return batchLog[identityId].length;
    }

    // ─────────────────────────────────────────────
    // KİMLİK DONDURMA (KILL SWITCH / ON-CHAIN FREEZE)
    // ─────────────────────────────────────────────

    /**
     * @notice Kimliği dondur — Kill Switch on-chain kaydı.
     *
     * Dondurulduktan sonra anchorMemory() çağrıları reddedilir.
     * genesisHash parametresi Genesis Anchor içeriklerinin SHA-256 hash'idir;
     * bu hash kaydedilerek ileride Genesis Anchors'ın değişmediği doğrulanabilir.
     *
     * @param identityId   Kimlik hash'i
     * @param genesisHash_ Genesis Anchor içeriklerinin SHA-256 hash'i
     */
    function freezeIdentity(
        bytes32 identityId,
        bytes32 genesisHash_
    ) external onlyGuardian(identityId) {
        require(!identities[identityId].isFrozen, "Kimlik zaten donduruldu");

        identities[identityId].isFrozen = true;
        identities[identityId].genesisHash = genesisHash_;
        identities[identityId].lastUpdate = block.timestamp;

        emit IdentityFrozen(identityId, genesisHash_, block.timestamp);
    }

    /**
     * @notice Dondurulmuş kimliği aktifleştir (kullanıcı isteğiyle unfreeze).
     *
     * Sadece guardian çağırabilir.
     * Kill Switch (admin freeze) ile dondurulmuş kimlikler için
     * guardian yetkisi yeterlidir — on-chain yetki ayrımı yapılmaz.
     *
     * @param identityId Kimlik hash'i
     */
    function unfreezeIdentity(
        bytes32 identityId
    ) external onlyGuardian(identityId) {
        require(identities[identityId].isFrozen, "Kimlik zaten aktif");
        identities[identityId].isFrozen = false;
        identities[identityId].lastUpdate = block.timestamp;
        emit IdentityUnfrozen(identityId, block.timestamp);
    }

    // ─────────────────────────────────────────────
    // OKUMA FONKSİYONLARI
    // ─────────────────────────────────────────────

    /**
     * @notice Kimlik bilgilerini getir
     */
    function getIdentity(bytes32 identityId)
        external
        view
        identityExists(identityId)
        returns (Identity memory)
    {
        return identities[identityId];
    }

    /**
     * @notice Hafıza log uzunluğunu getir
     */
    function getMemoryLogLength(bytes32 identityId)
        external
        view
        returns (uint256)
    {
        return memoryLog[identityId].length;
    }

    /**
     * @notice Son N hafıza anchor'ını getir
     * @param identityId Kimlik hash'i
     * @param count Kaç kayıt alınsın
     */
    function getRecentMemoryAnchors(bytes32 identityId, uint256 count)
        external
        view
        identityExists(identityId)
        returns (MemoryAnchor[] memory)
    {
        MemoryAnchor[] storage log = memoryLog[identityId];
        uint256 total = log.length;

        if (count >= total) {
            return log;
        }

        MemoryAnchor[] memory result = new MemoryAnchor[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = log[total - count + i];
        }
        return result;
    }

    /**
     * @notice Toplam kayıtlı kimlik sayısı
     */
    function totalIdentities() external view returns (uint256) {
        return registeredIdentities.length;
    }

    /**
     * @notice Karakter gücünü getir (gerçek değer: dönen / 100)
     */
    function getCharacterStrength(bytes32 identityId)
        external
        view
        returns (uint256)
    {
        return characterStrength[identityId];
    }
}
