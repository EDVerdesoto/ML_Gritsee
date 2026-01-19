def calcular_puntaje(datos):
    """
    Aplica las reglas de negocio del Molino para calificar la pizza.
    Retorna un diccionario con los puntajes desglosados y el total.
    """
    puntajes = {
        "burbujas": 0,
        "bordes": 0,
        "distribucion": 0,
        "horneado": 0,
        "grasa": 0,
        "total": 0,
        "veredicto": "FAIL"
    }

    # 1. Burbujas (30 pts si NO hay)
    if not datos['tiene_burbujas']:
        puntajes['burbujas'] = 30
    
    # 2. Bordes (15 pts si LIMPIOS)
    if datos['bordes_limpios']: # Ojo: tu variable debe ser 'limpios', no 'sucios'
        puntajes['bordes'] = 15

    # 3. Distribución (Escala variable)
    dist = datos['distribucion'].upper() # Asegurar mayúsculas
    mapa_distribucion = {
        "CORRECTO": 30,
        "ACEPTABLE": 20,
        "MEDIA": 15,
        "MALA": 5,
        "DEFICIENTE": 0
    }
    puntajes['distribucion'] = mapa_distribucion.get(dist, 0) # 0 por defecto si no coincide

    # 4. Horneado (Escala variable)
    horn = datos['horneado'].upper()
    mapa_horneado = {
        "CORRECTO": 15,
        "ALTO": 5,
        "BAJO": 5,
        "INSUFICIENTE": 0,
        "EXCESIVO": 0
    }
    puntajes['horneado'] = mapa_horneado.get(horn, 0)

    # 5. Grasa (10 pts si NO hay)
    if not datos['tiene_grasa']:
        puntajes['grasa'] = 10

    # TOTAL
    total = (puntajes['burbujas'] + puntajes['bordes'] + 
             puntajes['distribucion'] + puntajes['horneado'] + 
             puntajes['grasa'])
    
    puntajes['total'] = total

    # VEREDICTO (>= 75 es PASS)
    if total >= 75:
        puntajes['veredicto'] = "PASS"
    else:
        puntajes['veredicto'] = "FAIL"

    return puntajes