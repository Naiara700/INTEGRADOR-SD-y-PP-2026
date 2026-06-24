// utils/cryptoUtils.js
// Manejo seguro de llaves RSA usando la Web Crypto API nativa del navegador

const ALGORITHM = {
    name: "RSASSA-PKCS1-v1_5",
    hash: "SHA-256"
};

// Convierte un ArrayBuffer a Hexadecimal (para firmas)
function bufferToHex(buffer) {
    return Array.from(new Uint8Array(buffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

// Codifica un string base64 a formato PEM
function encodePem(base64, type = "PUBLIC") {
    const lines = base64.match(/.{1,64}/g).join('\n');
    return `-----BEGIN ${type} KEY-----\n${lines}\n-----END ${type} KEY-----`;
}

/**
 * Genera un par de claves RSA 2048-bit.
 * Retorna { privateKey (CryptoKey), publicKeyPem (string) }
 */
export async function generateWalletKeys() {
    const keyPair = await window.crypto.subtle.generateKey(
        { ...ALGORITHM, modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]) },
        true, // exportable
        ["sign", "verify"]
    );

    // Exportar clave pública a PEM (para enviar al backend)
    const exportedPublicKey = await window.crypto.subtle.exportKey("spki", keyPair.publicKey);
    const exportedPublicKeyBase64 = btoa(String.fromCharCode(...new Uint8Array(exportedPublicKey)));
    const publicKeyPem = encodePem(exportedPublicKeyBase64, "PUBLIC");

    return {
        privateKey: keyPair.privateKey,
        publicKeyPem: publicKeyPem
    };
}

/**
 * Firma un payload (diccionario/objeto) de forma determinista usando la Clave Privada.
 * Retorna la firma en formato Hexadecimal.
 */
export async function signTransaction(privateKey, payload) {
    // Es crucial que el string generado coincida con json.dumps(..., separators=(',', ':'), sort_keys=True) de Python
    // Implementaremos una serialización determinística simple:
    const sortedKeys = Object.keys(payload).sort();
    const sortedPayload = {};
    for (const key of sortedKeys) {
        sortedPayload[key] = payload[key];
    }
    const payloadStr = JSON.stringify(sortedPayload);
    const encoder = new TextEncoder();
    const data = encoder.encode(payloadStr);

    const signatureBuffer = await window.crypto.subtle.sign(
        ALGORITHM.name,
        privateKey,
        data
    );

    return bufferToHex(signatureBuffer);
}

// ==========================================
// Encriptación Local (AES-GCM + PBKDF2)
// Para proteger la clave privada con la contraseña del usuario
// ==========================================

async function getPasswordKey(password) {
    const enc = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
        "raw", enc.encode(password), { name: "PBKDF2" }, false, ["deriveBits", "deriveKey"]
    );
    return window.crypto.subtle.deriveKey(
        { name: "PBKDF2", salt: enc.encode("stickerchain_salt_2026"), iterations: 100000, hash: "SHA-256" },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
    );
}

export async function encryptPrivateKey(privateKey, password) {
    const exportedPrivateKey = await window.crypto.subtle.exportKey("pkcs8", privateKey);
    const aesKey = await getPasswordKey(password);
    
    // IV fijo para simplificar el prototipo (en prod debería ser aleatorio y guardado junto al cipher)
    const iv = new Uint8Array(12); 
    
    const encryptedBuffer = await window.crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        aesKey,
        exportedPrivateKey
    );
    
    return btoa(String.fromCharCode(...new Uint8Array(encryptedBuffer)));
}

export async function decryptPrivateKey(encryptedBase64, password) {
    const encryptedBytes = new Uint8Array(atob(encryptedBase64).split("").map(c => c.charCodeAt(0)));
    const aesKey = await getPasswordKey(password);
    const iv = new Uint8Array(12);
    
    try {
        const decryptedBuffer = await window.crypto.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            aesKey,
            encryptedBytes
        );
        
        return await window.crypto.subtle.importKey(
            "pkcs8",
            decryptedBuffer,
            ALGORITHM,
            true,
            ["sign"]
        );
    } catch (e) {
        throw new Error("Contraseña incorrecta o datos corruptos.");
    }
}


/**
 * Deriva la direccion publica (0x...) a partir del PEM de la clave publica.
 * Coincide con la logica del backend.
 */
export async function deriveAddress(publicKeyPem) {
    const encoder = new TextEncoder();
    const data = encoder.encode(publicKeyPem);
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return '0x' + hashHex.substring(0, 40);
}
