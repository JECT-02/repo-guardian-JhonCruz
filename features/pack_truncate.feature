Feature: Detección de packfiles truncados o corruptos

  Scenario: Packfile con firma inválida y CRC corrupto
    Given un repositorio con packfile corrupto "fixtures/pack-corrupt.git"
    When ejecuto el comando "guardian scan fixtures/pack-corrupt.git"
    Then el comando debe fallar con código de salida 2
    And la salida debe contener "Invalid packfile signature"
    And la salida debe contener "Invalid CRC at offset"