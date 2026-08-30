(define (problem mission)

  (:domain orbiter)

  ;; The target catalog.
  (:objects
    target-a target-b - target
  )

  ;; Everything is idle and nothing has been done yet.
  (:init
    (camera-free)
    (processor-free)
  )

  (:goal (and
    (processed target-a)
  ))
)
