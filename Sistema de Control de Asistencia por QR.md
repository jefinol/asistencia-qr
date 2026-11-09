# Sistema de Control de Asistencia por QR

Estoy cursando una materia llamada Programación III. Nos asignaron un proyecto final. Decidimos que era pertinente e innovador un sistema de control de asistencia por QR. Lo haremos de la forma más sencilla posible: un monolito. Será un proyecto sencillo en Flask o Fast API (dime tú cuál es el mejor para este caso). Habrán un sólo repo, tanto para el backend como para el frontend.

No caigamos en sobrecomplejidad y overengineering. Hagamos un sistema de control de asistencia funcional. Piensa en este proyecto como si fuera un MVP, pero para fines académicos. No utilizaremos metedologías SCRUM ni ningún marco de trabajo de project management porque simplemente es sobrecomplicar las cosas.

Usaremos docker, uv, venv para poder tener control de todo. Al final del proyecto podremos desplegarlo en un vps.

Para el frontend, tal vez Next.js o alguna otra alternativa más lightweight, sigo tu recomendación. Pero sí quiero que usemos React.

Ahora bien, te describo la especificación del proyecto:

El dominio de la aplicación son las secciones. Cada sección tiene un código alfanumérico que define el coordinador, y por supuesto el nombre de la asignatura, que también lo asigna el coordinador.

Los usuarios del sistema son el el coordinador, los docentes y los alumnos. El docente puede generar reportes que muestren estadísticas de porcentaje de asistencia. El coordinador ve la información de todas las secciones. Tiene un dashboard donde puede la información de cada sección bajo su cargo.

El coordinador debe cargar la matrícula de los estudiantes con los siguientes campos: nombres, apellidos, cédula. 

El docente desplegará el código QR en la pantalla que se mostrará en un proyector. Y los alumnos podrán escanearlo. El alumno escanea el código, que lo llevará a la aplicación y debe ingresar su cédula.

El docente tendrá dashboards donde verá las estadísticas de asistencia de su sección, así como generar reportes de las mismas en pdf o excel. El coordinador tendrá estadísticas generales de todas las secciones a su cargo y de cada sección particular cuando la escoja.

Define las estructuras de datos y algoritmos que usaremos para esto, y hazlo. Usaremos POO según aplique.

Documenta todas las decisiones de arquitectura, y por supuesto el código, para que mis otros compañeros puedan leerlo y entenderlo. NO HAGAMOS OVERENGINEERING.