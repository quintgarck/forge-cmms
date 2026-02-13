#!/usr/bin/env python
"""
Script para probar autenticación y creación de cliente
"""
import requests
import json

def test_complete_flow():
    """Probar el flujo completo de autenticación y creación de cliente"""
    base_url = "http://127.0.0.1:8000/api/v1/"
    
    print("=== PROBANDO FLUJO COMPLETO ===")
    
    # 1. Obtener token de autenticación
    print("\n1. Obteniendo token de autenticación...")
    
    login_data = {
        "username": "demo",
        "password": "demo123"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}auth/login/",
            json=login_data,
            timeout=10
        )
        
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get('access')
            print(f"✅ Token obtenido: {access_token[:30]}...")
            
            # 2. Crear cliente con autenticación
            print("\n2. Creando cliente con autenticación...")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            client_data = {
                "client_code": "TEST-FLOW-001",
                "type": "individual",
                "name": "Cliente Flujo Test",
                "email": "flujo@test.com",
                "phone": "1234567890",
                "address": "Dirección de prueba flujo",
                "credit_limit": 2000.00
            }
            
            create_response = requests.post(
                f"{base_url}clients/",
                json=client_data,
                headers=headers,
                timeout=10
            )
            
            print(f"Create client status: {create_response.status_code}")
            print(f"Create client response: {create_response.text}")
            
            if create_response.status_code == 201:
                client_result = create_response.json()
                print(f"✅ Cliente creado exitosamente: ID {client_result.get('client_id')}")
                
                # 3. Verificar que el cliente fue creado
                print("\n3. Verificando cliente creado...")
                
                client_id = client_result.get('client_id')
                get_response = requests.get(
                    f"{base_url}clients/{client_id}/",
                    headers=headers,
                    timeout=10
                )
                
                print(f"Get client status: {get_response.status_code}")
                
                if get_response.status_code == 200:
                    client_info = get_response.json()
                    print(f"✅ Cliente verificado: {client_info.get('name')}")
                    return True
                else:
                    print(f"❌ Error al verificar cliente: {get_response.text}")
                    return False
            else:
                print(f"❌ Error al crear cliente: {create_response.text}")
                return False
        else:
            print(f"❌ Error de login: {login_response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_health():
    """Probar endpoint de salud"""
    print("\n=== PROBANDO SALUD DEL SISTEMA ===")
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/health/", timeout=5)
        print(f"Health check: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Sistema saludable: {health_data}")
            return True
        else:
            print(f"❌ Sistema no saludable: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == '__main__':
    print("DIAGNÓSTICO COMPLETO DE REGISTRO DE CLIENTES")
    print("=" * 60)
    
    # Probar salud del sistema
    health_ok = test_health()
    
    # Probar flujo completo
    flow_ok = test_complete_flow()
    
    print("\n" + "=" * 60)
    print("RESUMEN FINAL:")
    print(f"Sistema saludable: {'✅' if health_ok else '❌'}")
    print(f"Flujo completo: {'✅' if flow_ok else '❌'}")
    
    if health_ok and flow_ok:
        print("\n🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("El registro de clientes está funcionando correctamente.")
    else:
        print("\n⚠️  Hay problemas que necesitan atención.")