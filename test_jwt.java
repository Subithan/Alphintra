import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import javax.crypto.SecretKey;
import java.time.Duration;

public class test_jwt {
    public static void main(String[] args) {
        String secret = "U29tZVZlcnlTdHJvbmdTZWNyZXRLZXlXaXRoRW5vdWdoQnl0ZXNGb3JFUjUxMkFsZ29yaXRobS0xMjM0NTY3ODkwYWJjZGVmZ2hpams=";
        String token = "eyJhbGciOiJIUzUxMiJ9.eyJyb2xlcyI6WyJVU0VSIl0sInN1YiI6InRlc3QxMCIsImlhdCI6MTc2MDgxNzk5MSwiZXhwIjoxNzYwOTA0MzkxfQ.jC5YHdGYQFbXWRXOTugYoK_lWBApLft9eTUk9Ut_k4woismozhezKhAsf3egtgSfPjzcRomr77i46LZsiww9MA";
        
        try {
            SecretKey signingKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(secret));
            
            Jws<Claims> claims = Jwts.parserBuilder()
                .setAllowedClockSkewSeconds(60)
                .setSigningKey(signingKey)
                .build()
                .parseClaimsJws(token);
                
            System.out.println("Token is valid!");
            System.out.println("Subject: " + claims.getBody().getSubject());
            System.out.println("Roles: " + claims.getBody().get("roles"));
            System.out.println("Issued At: " + claims.getBody().getIssuedAt());
            System.out.println("Expires At: " + claims.getBody().getExpiration());
            
        } catch (Exception e) {
            System.out.println("Token validation failed: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
