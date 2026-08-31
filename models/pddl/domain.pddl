(define (domain orbiter)

  (:requirements :strips :typing :durative-actions)

  (:types
    target
  )

  (:predicates
    ;; Mission state, one fact per target.
    (imaged ?t - target)      ; a raw image of the target is in onboard storage
    (processed ?t - target)   ; the image has been turned into a downlinkable product
    (downlinked ?t - target)  ; the product has reached the ground

    ;; Equipment state. The satellite carries one of each.
    (camera-free)
    (processor-free)
    (transmitter-free)
  )

  ;; Point the satellite at a target and take an image.
  (:durative-action observe
    :parameters (?t - target)
    :duration (= ?duration 5)
    :condition (over all (camera-free))
    :effect (at end (imaged ?t))
  )

  ;; Turn a raw image into a downlinkable product.
  ;; The processor is claimed at start and released at end.
  (:durative-action process
    :parameters (?t - target)
    :duration (= ?duration 2)
    :condition (and
      (at start (processor-free))
      (over all (imaged ?t))
    )
    :effect (and
      (at start (not (processor-free)))
      (at end (processor-free))
      (at end (processed ?t))
    )
  )

  ;; Transmit the processed product of one target to the ground.
  ;; The satellite carries a single transmitter.
  (:durative-action downlink
    :parameters (?t - target)

    ;; TODO(step 1): a transmission takes 3 time units.
    :duration (= ?duration todo-duration)

    ;; TODO(step 1): two conditions are needed.
    ;;   - the transmitter must be free when the transmission starts
    ;;   - the processed product of ?t must exist for the whole transmission
    :condition (and (at start (todo-conditions)))

    ;; TODO(step 1): three effects are needed.
    ;;   - claim the transmitter at start
    ;;   - release the transmitter at end
    ;;   - record at end that the product of ?t has reached the ground
    :effect (and (at end (todo-effects)))
  )
)
